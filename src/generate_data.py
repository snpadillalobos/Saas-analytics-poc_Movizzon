"""
generate_data.py
Generates realistic SaaS datasets for analytics proof-of-concept.
Simulates ~18 months of data for a mid-size SaaS company (~2,500 users).
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import os

fake = Faker()
np.random.seed(42)
random.seed(42)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
N_USERS       = 2500
START_DATE    = datetime(2023, 7, 1)
END_DATE      = datetime(2024, 12, 31)
DATE_RANGE    = (END_DATE - START_DATE).days

COUNTRIES = {
    "Chile": 0.30, "Mexico": 0.20, "Colombia": 0.15,
    "Argentina": 0.12, "Peru": 0.08, "Brazil": 0.07,
    "Spain": 0.05, "USA": 0.03
}

PLANS = {"Free": 0.55, "Basic": 0.30, "Pro": 0.15}

PLAN_PRICES = {"Free": 0, "Basic": 29, "Pro": 89}

FEATURES = [
    "dashboard_view", "report_export", "api_integration",
    "team_collaboration", "data_import", "custom_alerts",
    "advanced_filters", "scheduled_reports"
]

FEATURE_PLAN_ACCESS = {
    "Free":  ["dashboard_view", "data_import"],
    "Basic": ["dashboard_view", "data_import", "report_export",
              "advanced_filters", "custom_alerts"],
    "Pro":   FEATURES
}

EVENT_TYPES = ["login", "feature_use", "error", "upgrade", "downgrade",
               "logout", "support_ticket"]

# ─────────────────────────────────────────────
# 1. USERS
# ─────────────────────────────────────────────
def generate_users(n=N_USERS):
    rows = []
    country_choices = list(COUNTRIES.keys())
    country_weights = list(COUNTRIES.values())
    plan_choices    = list(PLANS.keys())
    plan_weights    = list(PLANS.values())

    for i in range(1, n + 1):
        signup_offset = random.randint(0, DATE_RANGE - 30)
        signup_date   = START_DATE + timedelta(days=signup_offset)
        plan          = random.choices(plan_choices, weights=plan_weights)[0]
        country       = random.choices(country_choices, weights=country_weights)[0]

        # Activity: Pro users more likely active, Free less
        activity_prob = {"Free": 0.52, "Basic": 0.71, "Pro": 0.88}
        is_active     = random.random() < activity_prob[plan]

        rows.append({
            "user_id":     f"U{i:05d}",
            "signup_date": signup_date.date(),
            "country":     country,
            "plan":        plan,
            "is_active":   is_active,
        })

    return pd.DataFrame(rows)

# ─────────────────────────────────────────────
# 2. EVENTS
# ─────────────────────────────────────────────
def generate_events(users_df):
    rows = []
    event_id = 1

    for _, user in users_df.iterrows():
        signup = pd.to_datetime(user["signup_date"])
        
        # Days active since signup (capped at END_DATE)
        days_since_signup = (END_DATE - signup).days
        if days_since_signup <= 0:
            continue

        # Session frequency depends on plan + activity
        base_sessions = {"Free": 1.2, "Basic": 3.5, "Pro": 7.0}
        multiplier    = 1.1 if user["is_active"] else 0.3
        n_sessions    = max(0, int(np.random.poisson(
            base_sessions[user["plan"]] * multiplier * (days_since_signup / 30)
        )))

        accessible = FEATURE_PLAN_ACCESS[user["plan"]]

        for _ in range(n_sessions):
            day_offset  = random.randint(0, days_since_signup)
            event_date  = signup + timedelta(days=day_offset)
            if event_date > END_DATE:
                continue

            # Login always present in a session
            rows.append({
                "event_id":    f"E{event_id:07d}",
                "user_id":     user["user_id"],
                "event_type":  "login",
                "event_date":  event_date.date(),
                "feature_name": None
            })
            event_id += 1

            # 1-4 feature uses per session
            n_features = random.randint(1, 4)
            for _ in range(n_features):
                feature = random.choice(accessible)
                rows.append({
                    "event_id":    f"E{event_id:07d}",
                    "user_id":     user["user_id"],
                    "event_type":  "feature_use",
                    "event_date":  event_date.date(),
                    "feature_name": feature
                })
                event_id += 1

            # Error rate: Free plans have higher error rates (worse onboarding)
            error_prob = {"Free": 0.18, "Basic": 0.10, "Pro": 0.05}
            if random.random() < error_prob[user["plan"]]:
                rows.append({
                    "event_id":    f"E{event_id:07d}",
                    "user_id":     user["user_id"],
                    "event_type":  "error",
                    "event_date":  event_date.date(),
                    "feature_name": random.choice(accessible)
                })
                event_id += 1

            # Upgrade events (Free → paid, low prob)
            if user["plan"] == "Free" and random.random() < 0.008:
                rows.append({
                    "event_id":    f"E{event_id:07d}",
                    "user_id":     user["user_id"],
                    "event_type":  "upgrade",
                    "event_date":  event_date.date(),
                    "feature_name": None
                })
                event_id += 1

    return pd.DataFrame(rows)

# ─────────────────────────────────────────────
# 3. TRANSACTIONS
# ─────────────────────────────────────────────
def generate_transactions(users_df):
    rows = []
    tx_id = 1

    paying_users = users_df[users_df["plan"].isin(["Basic", "Pro"])]

    for _, user in paying_users.iterrows():
        signup     = pd.to_datetime(user["signup_date"])
        price      = PLAN_PRICES[user["plan"]]
        months_active = max(1, (END_DATE - signup).days // 30)

        for m in range(months_active):
            tx_date = signup + timedelta(days=30 * m)
            if tx_date > END_DATE:
                break

            # 4% failed transaction rate
            status = "failed" if random.random() < 0.04 else "completed"

            # Small amount jitter for realism
            amount = price + random.uniform(-1.5, 1.5) if status == "completed" else 0

            rows.append({
                "transaction_id":   f"T{tx_id:07d}",
                "user_id":          user["user_id"],
                "amount":           round(amount, 2),
                "transaction_date": tx_date.date(),
                "status":           status
            })
            tx_id += 1

    return pd.DataFrame(rows)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    out = "/home/claude/saas_analytics/data/raw"
    os.makedirs(out, exist_ok=True)

    print("⏳ Generating users...")
    users = generate_users()
    users.to_csv(f"{out}/users.csv", index=False)
    print(f"   ✅ {len(users):,} users")

    print("⏳ Generating events...")
    events = generate_events(users)
    events.to_csv(f"{out}/events.csv", index=False)
    print(f"   ✅ {len(events):,} events")

    print("⏳ Generating transactions...")
    transactions = generate_transactions(users)
    transactions.to_csv(f"{out}/transactions.csv", index=False)
    print(f"   ✅ {len(transactions):,} transactions")

    print("\n✅ All datasets saved to", out)
