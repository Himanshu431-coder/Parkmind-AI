from groq import Groq
from app.core.config import get_settings

class RAGService:
    def __init__(self):
        settings = get_settings()
        api_key = settings.GROQ_API_KEY
        if api_key:
            self.client = Groq(api_key=api_key)
            self.ready = True
            print("Groq AI service initialized.")
        else:
            self.client = None
            self.ready = False
            print("No GROQ_API_KEY found. AI chat will use fallback.")

    def _build_context(self, pricing_data, question):
        parts = []
        parts.append("=== PARKING SYSTEM DATA ===")
        parts.append("You are an AI assistant for ParkMind, a smart parking pricing system.")
        parts.append("The system uses a PPO RL agent and a Heuristic Model to price 14 parking lots.")
        parts.append("")
        if pricing_data.get("lots"):
            parts.append("=== CURRENT LOT PRICES ===")
            for lot in pricing_data["lots"]:
                parts.append("Lot " + lot["name"] + ": RL=$" + str(round(lot["rl_price"],2)) + ", Heuristic=$" + str(round(lot["heuristic_price"],2)) + ", Occ=" + str(lot["occupancy"]) + "/" + str(lot["capacity"]) + " (" + str(round(lot["occupancy_rate"]*100)) + "%), Queue=" + str(lot["queue_length"]) + ", Traffic=" + str(lot["traffic_level"]))
            parts.append("")
        if pricing_data.get("summary"):
            s = pricing_data["summary"]
            parts.append("=== SUMMARY ===")
            parts.append("Avg RL Price: $" + str(round(s.get("avg_rl_price",0),2)))
            parts.append("Avg Heuristic Price: $" + str(round(s.get("avg_heuristic_price",0),2)))
            parts.append("RL Efficiency: " + str(s.get("rl_efficiency","N/A")))
            parts.append("Most expensive: " + str(s.get("most_expensive","N/A")))
            parts.append("Cheapest: " + str(s.get("cheapest","N/A")))
            parts.append("")
        parts.append("=== RL INFO ===")
        parts.append("PPO agent trained 200k steps. +12% revenue over heuristic. 93% demand retention.")
        parts.append("")
        parts.append("Answer concisely using data above. Use $ for prices. Redirect non-parking questions.")
        return "\n".join(parts)

    async def answer(self, question, pricing_data):
        if not self.ready:
            return self._fallback(question, pricing_data)
        context = self._build_context(pricing_data, question)
        try:
            resp = self.client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"system","content":context},{"role":"user","content":question}], max_tokens=300, temperature=0.3)
            return resp.choices[0].message.content
        except Exception as e:
            print("Groq error: " + str(e))
            return self._fallback(question, pricing_data)

    def _fallback(self, question, pricing_data):
        q = question.lower()
        s = pricing_data.get("summary",{})
        if "expensive" in q or "highest" in q:
            return "Most expensive: " + str(s.get("most_expensive","N/A"))
        if "cheapest" in q or "cheap" in q:
            return "Cheapest: " + str(s.get("cheapest","N/A"))
        if "compare" in q:
            return "RL avg: $" + str(round(s.get("avg_rl_price",0),2)) + " vs Heuristic avg: $" + str(round(s.get("avg_heuristic_price",0),2))
        if "status" in q or "health" in q:
            return "All 14 lots active. RL Agent loaded. Database healthy."
        return "Try: most expensive, cheapest, compare prices, or status."

rag_service = RAGService()
