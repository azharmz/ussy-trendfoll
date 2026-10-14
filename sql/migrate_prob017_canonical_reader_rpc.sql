-- PROB-017 canonical reader for public dashboard consumers.
-- The function is read-only and fails closed if any duplicate identity or
-- resolved ledger mapping is missing, stale, or inconsistent.
CREATE OR REPLACE FUNCTION public.get_canonical_position_history()
RETURNS SETOF public.positions
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
    bad_identity text;
BEGIN
    -- Every duplicate source identity must have exactly one valid resolved
    -- decision whose canonical/excluded IDs exactly partition the source IDs.
    SELECT format('%s/%s', d.symbol, d.entry_date)
      INTO bad_identity
      FROM (
          SELECT p.symbol, p.entry_date, array_agg(p.id ORDER BY p.id) AS position_ids
            FROM public.positions p
           GROUP BY p.symbol, p.entry_date
          HAVING count(*) > 1
      ) d
      LEFT JOIN LATERAL (
          SELECT
              count(*) FILTER (WHERE r.resolution_status = 'resolved') AS resolved_count,
              count(*) FILTER (
                  WHERE r.resolution_status = 'resolved'
                    AND r.canonical_position_id = ANY(d.position_ids)
                    AND (
                        SELECT array_agg(u.id ORDER BY u.id)
                          FROM unnest(r.excluded_position_ids) AS u(id)
                    ) = ARRAY(
                        SELECT u.id
                          FROM unnest(d.position_ids) AS u(id)
                         WHERE u.id <> r.canonical_position_id
                         ORDER BY u.id
                    )
              ) AS valid_count
            FROM public.position_identity_reconciliations r
           WHERE r.symbol = d.symbol
             AND r.entry_date = d.entry_date
      ) checks ON true
     WHERE coalesce(checks.resolved_count, 0) <> 1
        OR coalesce(checks.valid_count, 0) <> 1
     LIMIT 1;

    IF bad_identity IS NOT NULL THEN
        RAISE EXCEPTION 'PROB-017 canonical reader rejected unresolved or invalid identity: %', bad_identity;
    END IF;

    -- A resolved ledger row must still refer to an existing duplicate group
    -- and exactly match that group's current canonical/excluded IDs.
    SELECT format('%s/%s', r.symbol, r.entry_date)
      INTO bad_identity
      FROM public.position_identity_reconciliations r
     WHERE r.resolution_status = 'resolved'
       AND NOT EXISTS (
           SELECT 1
             FROM public.positions canonical
            WHERE canonical.id = r.canonical_position_id
              AND canonical.symbol = r.symbol
              AND canonical.entry_date = r.entry_date
              AND (
                  SELECT count(*)
                    FROM public.positions p
                   WHERE p.symbol = r.symbol
                     AND p.entry_date = r.entry_date
              ) > 1
              AND (
                  SELECT array_agg(p.id ORDER BY p.id)
                    FROM public.positions p
                   WHERE p.symbol = r.symbol
                     AND p.entry_date = r.entry_date
                     AND p.id <> r.canonical_position_id
              ) = (
                  SELECT array_agg(u.id ORDER BY u.id)
                    FROM unnest(r.excluded_position_ids) AS u(id)
              )
       )
     LIMIT 1;

    IF bad_identity IS NOT NULL THEN
        RAISE EXCEPTION 'PROB-017 canonical reader rejected stale reconciliation: %', bad_identity;
    END IF;

    RETURN QUERY
        SELECT p.*
          FROM public.positions p
         WHERE NOT EXISTS (
             SELECT 1
               FROM public.position_identity_reconciliations r
              WHERE r.symbol = p.symbol
                AND r.entry_date = p.entry_date
                AND r.resolution_status = 'resolved'
                AND p.id = ANY(r.excluded_position_ids)
         );
END;
$function$;

REVOKE ALL ON FUNCTION public.get_canonical_position_history() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.get_canonical_position_history() TO anon, authenticated;

COMMENT ON FUNCTION public.get_canonical_position_history() IS
    'Read-only PROB-017 canonical history for dashboard consumers; validates all duplicate identities and resolved ledger mappings, failing closed on inconsistency.';
