# STOP-EXEC-001 — CURRENT Gap-Through Execution Audit Protocol

Status: **FROZEN PRE-OUTCOME / DIAGNOSTIC ONLY / NO PRODUCTION CHANGE**

## Question

Quantify the execution bias in the frozen CURRENT production stop contract when a session opens below the operative fixed stop. CURRENT currently triggers on `low_raw <= stop_price` and records the fill exactly at `stop_price`; this audit asks how often that assumption is infeasible and how much it changes realized outcomes.

## Frozen corpus

Use the same deterministic development security sample and research-history contract as EXIT-ISO-001 / EXIT-CAND-003 development:

- deterministic SHA256-ranked first 100 securities from R2 READY
- evaluation boundary from the R2 READY snapshot
- research history with minimum 500-bar pre-roll
- canonical feature/decision pipeline
- eligible signal onsets only
- T+1 Open executable entry
- exact 45-forward-bar comparability

This is a diagnostic reuse of an already-governed corpus, not a new candidate-development sample.

## Frozen variants

Evaluate the exact same paired events under only two execution representations. No parameter changes are allowed.

### CURRENT_EXACT_STOP

Preserve existing production/backtest semantics:

1. entry = T+1 `open_raw`
2. fixed stop = entry − 2 × ATR14(T0)
3. if `low_raw <= stop`, fill exactly at stop
4. otherwise max-holding / EMA20 behavior remains unchanged
5. max holding = 45 trading sessions

### GAP_AWARE_DIAGNOSTIC

Change only the stop fill representation:

1. same entry, stop, EMA20 and max holding as CURRENT_EXACT_STOP
2. if `open_raw <= stop`, fill at observed Open and label `stop_loss_gap`
3. else if `low_raw <= stop`, fill exactly at stop and label `stop_loss_touch`
4. all other behavior remains identical

This variant is **diagnostic only**. It is not a proposed production change and is not a tunable candidate.

## Required outputs

- exact paired event count
- stop-event count under CURRENT
- gap-through count and fraction of CURRENT stop events
- touch count
- distribution of gap slippage `(open / stop - 1)` for gap-through events
- CURRENT vs gap-aware median realized return and positive rate
- paired realized-return delta distribution
- count/fraction of events whose outcome changes
- worst observed gap slippage
- event-level CSV with symbol, T0, entry, stop, exit day/reason/price and paired delta

## Interpretation

- If no gap-through events exist, STOP-EXEC-001 closes as **NO OBSERVED GAP-THROUGH IN GOVERNED CORPUS**.
- If gap-through events exist, the current exact-stop fill is an execution-feasibility defect for those events. Magnitude is reported descriptively; there is no optimization threshold.
- Any production correction requires a separate implementation/migration decision after this evidence is locked.

## Governance

- no tuning
- no alternative ATR multiple
- no alternative stop type
- no entry-rule change
- no EMA/max-hold change
- no production mutation from this audit
- EXIT-CAND-003 remains frozen and separate
