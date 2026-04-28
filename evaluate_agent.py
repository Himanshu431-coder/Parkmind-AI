# -*- coding: utf-8 -*-
"""Evaluate RL Agent vs Heuristic Model 2 on simulated scenarios."""
import numpy as np
from app.pricing.engine import pricing_engine

def evaluate(n_scenarios=1000):
    rl_revenues = []
    h_revenues = []
    rl_demand_retained = 0
    h_demand_retained = 0
    base = 10.0

    for _ in range(n_scenarios):
        capacity = np.random.randint(200, 600)
        occupancy = np.random.randint(int(capacity * 0.1), int(capacity * 0.95))
        queue = np.random.randint(0, 25)
        traffic = np.random.choice(["low", "average", "moderate", "high"])
        special = np.random.random() > 0.85
        vehicle = np.random.choice(["car", "bike", "truck", "cycle"])
        hour = np.random.randint(0, 24)
        day = np.random.randint(0, 7)

        rl_price, rl_demand, _ = pricing_engine.compute_price(
            occupancy, capacity, queue, traffic, special, vehicle, hour, day, use_rl=True
        )
        h_price, h_demand, _ = pricing_engine.compute_price(
            occupancy, capacity, queue, traffic, special, vehicle, hour, day, use_rl=False
        )

        occ_rate = occupancy / capacity
        rl_elasticity = max(0.6, 1 - (rl_price - base) / (base * 2.5))
        h_elasticity = max(0.6, 1 - (h_price - base) / (base * 2.5))
        base_sales = max(0, 1 - max(0, occ_rate - 0.9) * 3)
        rl_sales = base_sales * rl_elasticity
        h_sales = base_sales * h_elasticity

        rl_revenues.append(rl_price * rl_sales)
        h_revenues.append(h_price * h_sales)

        rl_retain_prob = max(0, min(1, 0.97 - (rl_price - base) / (base * 5.5)))
        h_retain_prob = max(0, min(1, 0.99 - (h_price - base) / (base * 5.5)))
        if np.random.random() < rl_retain_prob:
            rl_demand_retained += 1
        if np.random.random() < h_retain_prob:
            h_demand_retained += 1

    total_rl = sum(rl_revenues)
    total_h = sum(h_revenues)
    revenue_gain = ((total_rl - total_h) / total_h) * 100
    rl_retention = (rl_demand_retained / n_scenarios) * 100
    h_retention = (h_demand_retained / n_scenarios) * 100

    print("=" * 55)
    print("  PARKMIND - RL Agent Evaluation Report")
    print("=" * 55)
    print(f"  Scenarios evaluated:     {n_scenarios}")
    print(f"  RL Total Revenue:        ${total_rl:,.2f}")
    print(f"  Heuristic Total Revenue: ${total_h:,.2f}")
    print(f"  Revenue Gain:            {revenue_gain:+.1f}%")
    print(f"  RL Demand Retention:     {rl_retention:.1f}%")
    print(f"  H Demand Retention:      {h_retention:.1f}%")
    print("=" * 55)
    print(f"  VERDICT: RL agent generates {revenue_gain:+.1f}% more revenue")
    print(f"           while retaining {rl_retention:.0f}% of demand")
    print("=" * 55)

    return {
        "revenue_gain_pct": round(revenue_gain, 1),
        "rl_demand_retention": round(rl_retention, 1),
        "scenarios": n_scenarios,
    }

if __name__ == "__main__":
    evaluate(1000)
