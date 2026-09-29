-- ====================================================================
-- dbt Model 1: stg_incidents.sql (Staging layer: Clean and type cast)
-- ====================================================================
WITH raw_incidents AS (
    SELECT
        incident_id,
        service_name,
        severity,
        root_cause_summary,
        created_at,
        resolved_at,
        EXTRACT(EPOCH FROM (resolved_at - created_at)) / 60.0 AS duration_minutes
    FROM raw_incident_logs
)
SELECT
    incident_id,
    service_name,
    severity,
    duration_minutes,
    CASE 
        WHEN severity = 'P1' THEN 15.0 -- 15 min SLA target for P1
        WHEN severity = 'P2' THEN 60.0 -- 1 hour SLA target for P2
        ELSE 240.0                     -- 4 hours for P3/P4
    END AS sla_target_minutes,
    created_at
FROM raw_incidents;

-- ====================================================================
-- dbt Model 2: fct_service_reliability.sql (Data Mart: SRE KPIs)
-- ====================================================================
WITH incident_metrics AS (
    SELECT
        service_name,
        COUNT(incident_id) AS total_incidents,
        SUM(CASE WHEN severity = 'P1' THEN 1 ELSE 0 END) AS p1_incidents,
        ROUND(AVG(duration_minutes)::numeric, 1) AS mttr_minutes, -- Mean Time to Resolution
        ROUND(MIN(duration_minutes)::numeric, 1) AS min_resolution_minutes,
        ROUND(MAX(duration_minutes)::numeric, 1) AS max_resolution_minutes
    FROM {{ ref('stg_incidents') }}
    GROUP BY service_name
)
SELECT
    service_name,
    total_incidents,
    p1_incidents,
    mttr_minutes,
    CASE
        WHEN mttr_minutes <= 30.0 THEN 'EXCELLENT'
        WHEN mttr_minutes <= 60.0 THEN 'ACCEPTABLE'
        ELSE 'SLA_BREACH_RISK'
    END AS reliability_tier
FROM incident_metrics
ORDER BY total_incidents DESC;
