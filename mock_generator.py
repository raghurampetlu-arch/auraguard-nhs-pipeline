import time
import json
import random
import redis
from config import Config

# Connect directly to your local Redis instance
r = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)

print("🚀 Starting AuraGuard Mock Data Generator... Press Ctrl+C to stop.")

# Pre-populate some patient tokens on our digital ward map
patients = {
    101: {"x": 200, "y": 300},
    102: {"x": 450, "y": 700},
    103: {"x": 600, "y": 150}
}

try:
    while True:
        for p_id in patients.keys():
            # Gently simulate subtle human movement on a ward floor
            patients[p_id]["x"] += random.choice([-10, 0, 10])
            patients[p_id]["y"] += random.choice([-10, 0, 10])
            
            # Constrain to our custom matrix map boundaries
            patients[p_id]["x"] = max(50, min(750, patients[p_id]["x"]))
            patients[p_id]["y"] = max(50, min(950, patients[p_id]["y"]))
            
            # 5% chance a simulated patient undergoes a medical fall event
            is_fall = random.random() < 0.05
            status = "FALL_CRITICAL" if is_fall else "NORMAL"
            
            payload = {
                "patient_token": p_id,
                "ward_x": patients[p_id]["x"],
                "ward_y": patients[p_id]["y"],
                "status": status
            }
            
            # Broadcast the live tracking coordinates
            r.publish(Config.STREAM_CHANNEL, json.dumps(payload))
            
            # If a critical incident occurs, pass it down the emergency channel
            if is_fall:
                r.publish(Config.ALERT_CHANNEL, json.dumps(payload))
                print(f"🚨 Simulating Fall: Patient Token #{p_id}")
                
        time.sleep(0.5) # Emulate a half-second tracking interval frame loop
except KeyboardInterrupt:
    print("\n🛑 Mock generator stopped.")
