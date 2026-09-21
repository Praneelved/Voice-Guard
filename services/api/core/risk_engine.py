import asyncio
import time
import random
from schemas.events import RiskUpdateEvent, Signals

class RiskSimulator:
    def __init__(self, call_id: str):
        self.call_id = call_id
        self.current_risk = 0.1
        self.running = False
        
    async def run(self, send_func):
        self.running = True
        while self.running:
            # Gradually vary risk
            variation = random.uniform(-0.05, 0.10)
            self.current_risk = max(0.0, min(1.0, self.current_risk + variation))
            
            level = "low"
            if self.current_risk > 0.7:
                level = "high"
            elif self.current_risk > 0.4:
                level = "caution"
                
            event = RiskUpdateEvent(
                call_id=self.call_id,
                timestamp_ms=int(time.time() * 1000),
                risk=self.current_risk,
                level=level,
                confidence=0.85,
                quality="good",
                signals=Signals(
                    antispoof=self.current_risk * 1.1 if self.current_risk < 0.9 else 0.95,
                    speaker_mismatch=None,
                    signal_anomaly=random.uniform(0.1, 0.3)
                )
            )
            
            await send_func(event.model_dump_json())
            await asyncio.sleep(1)
            
    def stop(self):
        self.running = False
