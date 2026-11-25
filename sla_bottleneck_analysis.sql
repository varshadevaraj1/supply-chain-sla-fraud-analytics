-- ============================================================================
-- PROJECT: Supply Chain SLA Protection & Delivery Bottleneck Audit
-- AUTHOR: Varsha Devaraj
-- DATASET: DataCo Smart Supply Chain Dataset (Public Kaggle Benchmark)
-- ============================================================================

WITH delivery_metrics AS (
    SELECT
        order_id,
        order_date,
        shipping_mode,
        order_region,
        customer_id,
        days_for_shipping_real AS actual_days,
        days_for_shipment_scheduled AS scheduled_days,
        (days_for_shipping_real - days_for_shipment_scheduled) AS variance_days,
        CASE
            WHEN days_for_shipping_real <= days_for_shipment_scheduled THEN 'On-Time'
            WHEN (days_for_shipping_real - days_for_shipment_scheduled) BETWEEN 1 AND 2 THEN 'Minor Delay'
            ELSE 'Critical SLA Breach'
        END AS sla_status,
        order_status,
        sales,
        order_item_discount_rate
    FROM supply_chain_orders
    WHERE order_status NOT IN ('CANCELED')
)

-- 1. Regional & Shipping Mode SLA Scorecard (Weekly Business Review View)
SELECT
    order_region,
    shipping_mode,
    COUNT(order_id) AS total_shipments,
    ROUND(
        100.0 * SUM(CASE WHEN sla_status = 'On-Time' THEN 1 ELSE 0 END) / COUNT(order_id),
        2
    ) AS on_time_sla_pct,
    SUM(CASE WHEN sla_status = 'Critical SLA Breach' THEN 1 ELSE 0 END) AS critical_breaches,
    ROUND(AVG(variance_days), 2) AS avg_delay_variance_days,
    RANK() OVER (
        PARTITION BY shipping_mode
        ORDER BY (100.0 * SUM(CASE WHEN sla_status = 'On-Time' THEN 1 ELSE 0 END) / COUNT(order_id)) ASC
    ) AS bottleneck_risk_rank
FROM delivery_metrics
GROUP BY order_region, shipping_mode
HAVING COUNT(order_id) >= 50
ORDER BY shipping_mode, bottleneck_risk_rank;
