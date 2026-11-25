import pandas as pd
import numpy as np

def run_supply_chain_pipeline(filepath: str):
    """
    Automated ETL & Anomaly Detection Pipeline:
    1. Cleans raw transactional logistics data
    2. Flags suspicious/fraud-risk accounts & route anomalies
    3. Exports an automated WBR (Weekly Business Review) summary CSV
    """
    # Load dataset (DataCoSupplyChainDataset.csv)
    df = pd.read_csv(filepath, encoding="ISO-8859-1")

    # Standardize column names
    df.columns = [c.strip().lower().replace(" ", "_").replace("(", "").replace(")", "") for c in df.columns]

    # Calculate SLA variance
    df["sla_variance"] = df["days_for_shipping_real"] - df["days_for_shipment_scheduled"]
    df["is_sla_breach"] = np.where(df["sla_variance"] > 1, 1, 0)

    # Flag potential fraud / operational anomalies:
    # Rule 1: Officially flagged SUSPECTED_FRAUD status
    # Rule 2: High discount rate (>20%) combined with negative profit & late delivery
    df["fraud_risk_flag"] = np.where(
        (df["order_status"] == "SUSPECTED_FRAUD") |
        ((df["order_item_discount_rate"] > 0.20) & (df["order_profit_per_order"] < 0) & (df["is_sla_breach"] == 1)),
        1,
        0
    )

    # Aggregate into Executive WBR Scorecard by Shipping Mode
    wbr_summary = (
        df.groupby("shipping_mode", as_index=False)
        .agg(
            total_orders=("order_id", "nunique"),
            on_time_rate_pct=("is_sla_breach", lambda x: round((1 - x.mean()) * 100, 2)),
            avg_delay_days=("sla_variance", lambda x: round(x.mean(), 2)),
            flagged_anomalies=("fraud_risk_flag", "sum"),
            revenue_at_risk=("sales", lambda x: round(x[df.loc[x.index, "fraud_risk_flag"] == 1].sum(), 2))
        )
        .sort_values(by="flagged_anomalies", ascending=False)
    )

    # Export clean WBR report for BI dashboard ingestion
    wbr_summary.to_csv("wbr_weekly_executive_summary.csv", index=False)
    print("Pipeline complete. WBR Summary generated:\n", wbr_summary)

if __name__ == "__main__":
    run_supply_chain_pipeline("DataCoSupplyChainDataset.csv")
