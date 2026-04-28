"""Train PPO agent for parking pricing."""
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pandas as pd
from stable_baselines3 import PPO
import os

class ParkingEnv(gym.Env):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.idx = 0
        self.action_space = spaces.Box(low=np.array([0.5]), high=np.array([2.0]), dtype=np.float32)
        self.observation_space = spaces.Box(low=0, high=1, shape=(8,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.idx = 0
        return self._get_obs(), {}

    def _get_obs(self):
        row = self.data.iloc[self.idx % len(self.data)]
        return np.array([
            row.get("occupancy_rate", 0.5),
            row.get("queue_length", 5) / 50,
            row.get("traffic_score", 0.5),
            row.get("is_special_day", 0),
            row.get("hour", 12) / 23,
            row.get("day_of_week", 2) / 6,
            row.get("vehicle_weight", 0.6),
            0.5
        ], dtype=np.float32)

    def step(self, action):
        row = self.data.iloc[self.idx % len(self.data)]
        base = 10.0
        price = base * float(action[0])
        occ = row.get("occupancy_rate", 0.5)
        revenue = price * (1 - max(0, occ - 0.9) * 5)
        demand_penalty = max(0, 0.3 - occ) * 50
        reward = revenue - demand_penalty
        self.idx += 1
        done = self.idx >= len(self.data)
        return self._get_obs(), float(reward), done, False, {}

if __name__ == "__main__":
    print("Training PPO agent...")
    n_samples = 2000
    data = pd.DataFrame({
        "occupancy_rate": np.random.uniform(0.2, 1.0, n_samples),
        "queue_length": np.random.randint(0, 30, n_samples),
        "traffic_score": np.random.uniform(0.2, 1.0, n_samples),
        "is_special_day": np.random.choice([0, 1], n_samples, p=[0.85, 0.15]),
        "hour": np.random.randint(0, 24, n_samples),
        "day_of_week": np.random.randint(0, 7, n_samples),
        "vehicle_weight": np.random.choice([0.5, 0.7, 1.0, 1.3], n_samples),
    })
    env = ParkingEnv(data)
    model = PPO("MlpPolicy", env, verbose=1, learning_rate=3e-4, n_steps=2048, batch_size=64, n_epochs=10)
    model.learn(total_timesteps=200000)
    save_path = os.path.join(os.path.dirname(__file__), "app", "pricing", "ppo_parking_agent")
    model.save(save_path)
    print(f"Model saved to {save_path}.zip")
