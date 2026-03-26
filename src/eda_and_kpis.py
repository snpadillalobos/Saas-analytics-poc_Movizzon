"""
eda_and_kpis.py
Exploratory Data Analysis + KPI computation for SaaS Analytics PoC.
Outputs: processed CSVs + printed insight summaries.
"""

import pandas as pd
import numpy as np
import json
import os
import warnings
warnings.filterwarnings("ignore")

RAW  = "/home/claude/saas_analytics/data/raw"
PROC = "/home/claude/saas_analytics/data/processed"
os.makedirs(PROC, exist_ok=True)

# ─────────────────────────────────────────────
# LOAD & VALIDATE
# ─────────────────────────────────────────────
print("=" * 60)
print("PHASE 1: DATA LOADING & VALIDATION")
print("=" * 60)

users  = pd.read_csv(f"{RAW}/users.csv",        parse_dates=["signup_date"])
events = pd.read_csv(f"{RAW}/events.csv",        parse_dates=["event_date"])
txns   = pd.read_csv(f"{RAW}/transactions.csv",  parse_dates=["transaction_date"])

print(f"\nusers.csv       → {len(users):>7,} rows | {users.isnull().sum().sum()} nulls")
print(f"events.csv      → {len(events):>7,} rows | {events.isnull().sum().sum()} nulls (feature_name expected)")
print(f"transactions.csv→ {len(txns):>7,} rows | {txns.isnull().sum().sum()} nulls")

# Validate referential integrity
orphan_events = events[~events["user_id"].isin(users["user_id"])]
orphan_txns   = txns[~txns["user_id"].isin(users["user_id"])]
print(f"\nOrphan events : {len(orphan_events)}")
print(f"Orphan txns   : {len(orphan_txns)}")

# ─────────────────────────────────────────────
# PHASE 2: KPIs
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("PHASE 2: KPI COMPUTATION")
print("=" * 60)

# ── KPI 1: User Base & Activation ──────────────────────────────
total_users   = len(users)
active_users  = users["is_active"].sum()
inactive_users = total_users - active_users
activation_rate = active_users / total_users

print(f"\n[KPI 1 — User Base]")
print(f"  Total Users    : {total_users:,}")
print(f"  Active         : {active_users:,}  ({activation_rate:.1%})")
print(f"  Inactive       : {inactive_users:,}  ({1-activation_rate:.1%})")

# ── KPI 2: Plan Distribution & MRR ────────────────────────────
plan_dist = users.groupby("plan").agg(
    count=("user_id","count"),
    active=("is_active","sum")
).reset_index()
plan_dist["pct_total"]  = plan_dist["count"] / total_users
plan_dist["active_rate"] = plan_dist["active"] / plan_dist["count"]

PLAN_PRICES = {"Free": 0, "Basic": 29, "Pro": 89}
plan_dist["price"] = plan_dist["plan"].map(PLAN_PRICES)
plan_dist["theoretical_mrr"] = plan_dist["active"] * plan_dist["price"]

real_mrr = txns[txns["status"]=="completed"].groupby(
    txns["transaction_date"].dt.to_period("M")
)["amount"].sum()
last_3m_mrr = real_mrr.tail(3).mean()

print(f"\n[KPI 2 — Plans & Revenue]")
print(plan_dist[["plan","count","pct_total","active_rate","theoretical_mrr"]].to_string(index=False))
print(f"\n  Avg MRR (last 3 months): ${last_3m_mrr:,.0f}")

# ── KPI 3: Feature Adoption ────────────────────────────────────
feature_events = events[events["event_type"]=="feature_use"]
feature_adoption = feature_events.groupby("feature_name").agg(
    total_uses=("event_id","count"),
    unique_users=("user_id","nunique")
).reset_index().sort_values("total_uses", ascending=False)
feature_adoption["adoption_rate"] = feature_adoption["unique_users"] / active_users

print(f"\n[KPI 3 — Feature Adoption (top features)]")
print(feature_adoption.head(8).to_string(index=False))

# ── KPI 4: Error Rate & Friction ──────────────────────────────
error_events  = events[events["event_type"]=="error"]
total_sessions = events[events["event_type"]=="login"]["user_id"].count()
error_rate    = len(error_events) / total_sessions

error_by_plan = events[events["event_type"].isin(["login","error"])].merge(
    users[["user_id","plan"]], on="user_id"
).groupby(["plan","event_type"]).size().unstack(fill_value=0)
error_by_plan["error_rate"] = error_by_plan["error"] / error_by_plan["login"]

print(f"\n[KPI 4 — Error & Friction]")
print(f"  Global Error Rate: {error_rate:.2%}")
print(error_by_plan[["error","login","error_rate"]].to_string())

# ── KPI 5: Transaction Success Rate ───────────────────────────
tx_summary = txns.groupby("status")["transaction_id"].count()
tx_success_rate = tx_summary.get("completed",0) / len(txns)
revenue_total = txns[txns["status"]=="completed"]["amount"].sum()

print(f"\n[KPI 5 — Transaction Health]")
print(f"  Success Rate  : {tx_success_rate:.2%}")
print(f"  Failed Txns   : {tx_summary.get('failed',0):,}")
print(f"  Total Revenue : ${revenue_total:,.0f}")

# ── KPI 6: Cohort Retention (simplified) ──────────────────────
users["signup_month"] = users["signup_date"].dt.to_period("M")
events_enriched = events.merge(users[["user_id","signup_month","plan"]], on="user_id")
events_enriched["event_month"] = events_enriched["event_date"].dt.to_period("M")
events_enriched["months_since_signup"] = (
    events_enriched["event_month"] - events_enriched["signup_month"]
).apply(lambda x: x.n)

# Users who logged in at month 0, 1, 3, 6
login_events = events_enriched[events_enriched["event_type"]=="login"]
cohort_base  = login_events[login_events["months_since_signup"]==0]["user_id"].nunique()

retention = {}
for m in [0, 1, 3, 6, 12]:
    retained = login_events[login_events["months_since_signup"]==m]["user_id"].nunique()
    retention[f"M{m}"] = f"{retained/cohort_base:.1%}" if cohort_base > 0 else "N/A"

print(f"\n[KPI 6 — Cohort Retention]")
for k,v in retention.items():
    print(f"  {k}: {v}")

# ── KPI 7: Geography ──────────────────────────────────────────
geo = users.groupby("country").agg(
    users=("user_id","count"),
    active=("is_active","sum"),
    pro_users=("plan", lambda x: (x=="Pro").sum())
).reset_index()
geo["active_rate"] = geo["active"] / geo["users"]
geo["pro_rate"]    = geo["pro_users"] / geo["users"]
geo = geo.sort_values("users", ascending=False)

print(f"\n[KPI 7 — Geography]")
print(geo.to_string(index=False))

# ── KPI 8: Monthly Revenue Trend ──────────────────────────────
monthly_rev = txns[txns["status"]=="completed"].copy()
monthly_rev["month"] = monthly_rev["transaction_date"].dt.to_period("M")
monthly_rev_agg = monthly_rev.groupby("month")["amount"].sum().reset_index()
monthly_rev_agg.columns = ["month", "revenue"]
monthly_rev_agg["month"] = monthly_rev_agg["month"].astype(str)

print(f"\n[KPI 8 — Monthly Revenue (last 6 months)]")
print(monthly_rev_agg.tail(6).to_string(index=False))

# ── KPI 9: Upgrade Funnel ─────────────────────────────────────
upgrades = events[events["event_type"]=="upgrade"]["user_id"].nunique()
free_users = users[users["plan"]=="Free"]
upgrade_cvr = upgrades / len(free_users)

print(f"\n[KPI 9 — Upgrade Funnel]")
print(f"  Free Users     : {len(free_users):,}")
print(f"  Upgrade Events : {upgrades:,}")
print(f"  Upgrade CVR    : {upgrade_cvr:.2%}")

# ── KPI 10: Power Users ────────────────────────────────────────
user_sessions = events[events["event_type"]=="login"].groupby("user_id").size().reset_index()
user_sessions.columns = ["user_id","sessions"]
p90 = user_sessions["sessions"].quantile(0.9)
power_users = user_sessions[user_sessions["sessions"] >= p90].merge(
    users[["user_id","plan"]], on="user_id"
)
power_plan = power_users["plan"].value_counts(normalize=True)

print(f"\n[KPI 10 — Power Users (top 10% by sessions)]")
print(f"  P90 session threshold: {p90:.0f} sessions")
print(power_plan.to_string())

# ─────────────────────────────────────────────
# SAVE PROCESSED OUTPUTS
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("PHASE 3: SAVING PROCESSED DATA")
print("=" * 60)

# Monthly revenue
monthly_rev_agg.to_csv(f"{PROC}/monthly_revenue.csv", index=False)

# Feature adoption
feature_adoption.to_csv(f"{PROC}/feature_adoption.csv", index=False)

# Plan summary
plan_dist.to_csv(f"{PROC}/plan_summary.csv", index=False)

# Geo summary
geo.to_csv(f"{PROC}/geo_summary.csv", index=False)

# Error by plan
error_by_plan.reset_index().to_csv(f"{PROC}/error_by_plan.csv")

# Users enriched (for Power BI)
users_enriched = users.merge(
    user_sessions, on="user_id", how="left"
).fillna({"sessions": 0})
users_enriched.to_csv(f"{PROC}/users_enriched.csv", index=False)

# Transactions enriched
txns_enriched = txns.merge(users[["user_id","plan","country"]], on="user_id", how="left")
txns_enriched.to_csv(f"{PROC}/transactions_enriched.csv", index=False)

# Events enriched (sample for BI — full file can be large)
events_enriched.to_csv(f"{PROC}/events_enriched.csv", index=False)

# KPI Summary JSON
kpi_summary = {
    "total_users": int(total_users),
    "active_users": int(active_users),
    "activation_rate": round(float(activation_rate), 4),
    "avg_mrr_last3m": round(float(last_3m_mrr), 2),
    "total_revenue": round(float(revenue_total), 2),
    "tx_success_rate": round(float(tx_success_rate), 4),
    "global_error_rate": round(float(error_rate), 4),
    "upgrade_cvr": round(float(upgrade_cvr), 4),
    "retention": retention
}
with open(f"{PROC}/kpi_summary.json", "w") as f:
    json.dump(kpi_summary, f, indent=2)

print("\nFiles saved to", PROC)
for f in os.listdir(PROC):
    print(f"  ✅ {f}")

print("\n✅ EDA complete.")
