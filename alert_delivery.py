"""Persistent alert-event and delivery ledger for PROB-003/004.

Event identity is semantic and transport-independent. Database uniqueness
arbitrates concurrent producers; a short delivery lease prevents normal
concurrent/rerun duplicate sends while allowing recovery after a crashed worker.
"""
from __future__ import annotations
import hashlib
import json
import uuid
from datetime import datetime, timezone, timedelta
import notify

EVENT_CONTRACT_VERSION = "trendfoll-alert-transition-v1"
TRANSPORT = "telegram"
LEASE_MINUTES = 15

def canonical_event_key(event: dict) -> str:
    required = ["symbol","as_of_date","event","previous_state","current_state"]
    missing=[k for k in required if not event.get(k)]
    if missing:
        raise ValueError(f"Malformed alert event identity; missing {missing}")
    identity={
        "contract_version":EVENT_CONTRACT_VERSION,
        "symbol":str(event["symbol"]),
        "effective_date":str(event["as_of_date"]),
        "transition_type":str(event["event"]),
        "from_state":str(event["previous_state"]),
        "to_state":str(event["current_state"]),
    }
    return hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def _record_event(client,event):
    key=canonical_event_key(event)
    row={
        "event_key":key,"contract_version":EVENT_CONTRACT_VERSION,
        "symbol":str(event["symbol"]),"effective_date":str(event["as_of_date"]),
        "transition_type":str(event["event"]),"from_state":str(event["previous_state"]),
        "to_state":str(event["current_state"]),"source_previous_date":event.get("previous_date"),
        "payload":{k:(float(v) if k=="close_raw" and v is not None else v) for k,v in event.items()},
    }
    client.table("alert_events").upsert(row,on_conflict="event_key",ignore_duplicates=True).execute()
    got=client.table("alert_events").select("*").eq("event_key",key).limit(2).execute().data or []
    if len(got)!=1: raise RuntimeError(f"Alert event identity did not resolve uniquely: {key}")
    print(f"[alert ledger] {'NEW/EXISTING'} EVENT {key[:12]} {event['symbol']} {event['event']}")
    return got[0]

def _ensure_delivery(client,event_id):
    client.table("alert_deliveries").upsert(
        {"event_id":event_id,"transport":TRANSPORT,"status":"pending"},
        on_conflict="event_id,transport",ignore_duplicates=True).execute()
    rows=client.table("alert_deliveries").select("*").eq("event_id",event_id).eq("transport",TRANSPORT).limit(2).execute().data or []
    if len(rows)!=1: raise RuntimeError(f"Delivery identity did not resolve uniquely for event {event_id}")
    return rows[0]

def _claim(client,delivery):
    if delivery["status"]=="delivered":
        print(f"[alert ledger] ALREADY DELIVERED / SKIP event={delivery['event_id']}")
        return None
    now=datetime.now(timezone.utc)
    token=str(uuid.uuid4())
    q=client.table("alert_deliveries").update({
        "status":"sending","claim_token":token,"claimed_at":now.isoformat(),"last_error":None
    }).eq("id",delivery["id"])
    if delivery["status"] in ("pending","failed"):
        q=q.eq("status",delivery["status"])
    elif delivery["status"]=="sending":
        claimed=delivery.get("claimed_at")
        if claimed:
            old=datetime.fromisoformat(str(claimed).replace("Z","+00:00"))
            if old > now-timedelta(minutes=LEASE_MINUTES):
                print(f"[alert ledger] DELIVERY IN-FLIGHT / SKIP event={delivery['event_id']}")
                return None
        q=q.eq("status","sending").eq("claim_token",delivery.get("claim_token"))
    else:
        raise RuntimeError(f"Unknown delivery status: {delivery['status']}")
    rows=q.execute().data or []
    if len(rows)!=1:
        print(f"[alert ledger] DELIVERY CLAIM LOST / SKIP event={delivery['event_id']}")
        return None
    return rows[0]

def _attempt(client,delivery,claim,event):
    attempt_id=str(uuid.uuid4())
    client.table("alert_delivery_attempts").insert({
        "attempt_id":attempt_id,"delivery_id":delivery["id"],"event_id":delivery["event_id"],
        "transport":TRANSPORT,"status":"attempted"
    }).execute()
    print(f"[alert ledger] DELIVERY ATTEMPT event={delivery['event_id']} attempt={attempt_id}")
    try:
        ack=notify.send_transition_event(event)
    except Exception as exc:
        err=f"{type(exc).__name__}: {exc}"[:1000]
        client.table("alert_delivery_attempts").update({"status":"failed","finished_at":datetime.now(timezone.utc).isoformat(),"error":err}).eq("attempt_id",attempt_id).execute()
        client.table("alert_deliveries").update({"status":"failed","last_error":err,"claim_token":None,"claimed_at":None}).eq("id",delivery["id"]).eq("claim_token",claim["claim_token"]).execute()
        print(f"[alert ledger] RETRYABLE FAILURE event={delivery['event_id']}: {err}")
        return False
    client.table("alert_delivery_attempts").update({
        "status":"delivered","finished_at":datetime.now(timezone.utc).isoformat(),"external_message_id":str(ack.get("message_id")) if ack.get("message_id") is not None else None
    }).eq("attempt_id",attempt_id).execute()
    updated=client.table("alert_deliveries").update({
        "status":"delivered","delivered_at":datetime.now(timezone.utc).isoformat(),"external_message_id":str(ack.get("message_id")) if ack.get("message_id") is not None else None,
        "last_error":None,"claim_token":None,"claimed_at":None
    }).eq("id",delivery["id"]).eq("claim_token",claim["claim_token"]).execute().data or []
    if len(updated)!=1: raise RuntimeError("Telegram acknowledged but delivery success marker was not persisted")
    print(f"[alert ledger] DELIVERED event={delivery['event_id']} message_id={ack.get('message_id')}")
    return True

def persist_and_deliver_transitions(client,transitions):
    for event in transitions:
        persisted=_record_event(client,event)
        delivery=_ensure_delivery(client,persisted["id"])
        claim=_claim(client,delivery)
        if claim is not None: _attempt(client,delivery,claim,event)
