import numpy as np
from app.core.config import get_settings
from stable_baselines3 import PPO
import os

settings = get_settings()

class PricingEngine:
    ALPHA = 0.6
    BETA = 0.4
    GAMMA = 0.2
    DELTA = 0.1
    VEHICLE_WEIGHTS = {"car": 1.0, "bike": 0.7, "truck": 1.3, "cycle": 0.5}
    TRAFFIC_SCORES = {"low": 0.3, "average": 0.5, "moderate": 0.6, "high": 1.0}

    def __init__(self):
        self.rl_model = None
        self.rl_loaded = False
        self._load_rl_model()

    def _load_rl_model(self):
        model_path = os.path.join(os.path.dirname(__file__), "ppo_parking_agent")
        if os.path.exists(model_path + ".zip"):
            try:
                self.rl_model = PPO.load(model_path)
                self.rl_loaded = True
                print("RL agent loaded successfully.")
            except Exception as e:
                print("Could not load RL agent: " + str(e))
        else:
            print("No RL agent found. Using Model 2 fallback.")

    def compute_price(self, occupancy, capacity, queue_length, traffic_level, is_special_day, vehicle_type, hour=12, day_of_week=2, use_rl=True):
        if use_rl and self.rl_loaded:
            return self._compute_rl(occupancy, capacity, queue_length, traffic_level, is_special_day, vehicle_type, hour, day_of_week)
        return self._compute_heuristic(occupancy, capacity, queue_length, traffic_level, is_special_day, vehicle_type)

    def _compute_rl(self, occupancy, capacity, queue_length, traffic_level, is_special_day, vehicle_type, hour, day_of_week):
        base = settings.BASE_PRICE
        traffic_enc = {"low": 0.0, "average": 0.5, "moderate": 0.6, "high": 1.0}.get(traffic_level, 0.5)
        vehicle_enc = {"cycle": 0.1, "bike": 0.3, "car": 0.6, "truck": 1.0}.get(vehicle_type, 0.6)
        obs = np.array([occupancy / max(capacity, 1), queue_length, traffic_enc, float(is_special_day), hour / 23.0, day_of_week / 6.0, vehicle_enc, base / (2.0 * base)], dtype=np.float32)
        action, _ = self.rl_model.predict(obs, deterministic=True)
        multiplier = float(np.clip(action[0], 0.5, 2.0))
        price = round(base * multiplier, 2)
        demand = 0.6 * (occupancy / max(capacity, 1)) + 0.4 * (queue_length / 50.0) + 0.2 * traffic_enc + 0.1 * float(is_special_day) + 0.1 * {"cycle": 0.5, "bike": 0.7, "car": 1.0, "truck": 1.3}.get(vehicle_type, 1.0)
        demand_score = round(np.clip(demand / 2.0, 0, 1), 4)
        return price, demand_score, "rl_ppo_agent"

    def _compute_heuristic(self, occupancy, capacity, queue_length, traffic_level, is_special_day, vehicle_type):
        base = settings.BASE_PRICE
        occ_rate = occupancy / max(capacity, 1)
        demand = self.ALPHA * occ_rate + self.BETA * (queue_length / 50.0) + self.GAMMA * self.TRAFFIC_SCORES.get(traffic_level, 0.5) + self.DELTA * float(is_special_day) + 0.1 * self.VEHICLE_WEIGHTS.get(vehicle_type, 1.0)
        normalized_demand = np.clip(demand / 2.0, 0, 1)
        multiplier = 0.5 + (1.5 * normalized_demand)
        price = round(base * multiplier, 2)
        return price, round(normalized_demand, 4), "model_2_demand"

pricing_engine = PricingEngine()
