import paho.mqtt.client as mqtt
import time
import json
import random

# ==========================================
# HVAC Simulator Configuration (3 Rooms)
# ==========================================
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
TOPIC_SUB = "hvac/room/+/actuators" # Wildcard to listen for all rooms

# Room IDs to simulate
ROOMS = ["RM-401", "RM-402", "RM-403"]

# Dictionary to keep independent states for each room
room_states = {
    room_id: {
        "ac_mode": "NORMAL",
        "ac_temp": 24.0,
        "current_temp": 24.5 + random.uniform(-1, 1)
    } for room_id in ROOMS
}

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"✅ Connected to MQTT Broker: {MQTT_BROKER}")
        client.subscribe(TOPIC_SUB)
        print(f"📡 Listening for AI Commands on: {TOPIC_SUB}")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    try:
        raw_payload = msg.payload.decode()
        # Topic format: hvac/room/RM-401/actuators
        parts = msg.topic.split('/')
        if len(parts) >= 3:
            room_id = parts[2]
            if room_id in room_states:
                command_data = json.loads(raw_payload)
                print(f"\n📥 AI Command for {room_id}: {raw_payload}")
                
                # Update room state
                if "command" in command_data:
                    room_states[room_id]["ac_mode"] = command_data.get("command")
                    room_states[room_id]["ac_temp"] = command_data.get("set_temp", room_states[room_id]["ac_temp"])
                    print(f"✨ {room_id} Updated: Mode={room_states[room_id]['ac_mode']}, Temp={room_states[room_id]['ac_temp']}°C")

    except Exception as e:
        print(f"❌ Error processing AI command: {e}")

def run_simulator():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print(f"🚀 Starting HVAC Multi-Room Simulator: {', '.join(ROOMS)}")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()

        while True:
            for room_id in ROOMS:
                state = room_states[room_id]
                
                # Simulation Logic
                if state["ac_mode"] == "OFF":
                    state["current_temp"] += random.uniform(0.01, 0.05)
                else:
                    # Move towards target temp (Faster response for demo: 0.3 factor)
                    target = state["ac_temp"]
                    diff = target - state["current_temp"]
                    state["current_temp"] += diff * 0.3 + random.uniform(-0.02, 0.02)

                sensor_data = {
                    "room_id": room_id,
                    "temperature": round(state["current_temp"], 2),
                    "humidity": random.randint(45, 65),
                    "occupancy": (random.randint(1,5)) if random.random() > 0.4 else 0,
                    "co2_ppm": random.randint(400, 1100),
                    "hvac_status": state["ac_mode"],
                    "set_temperature": state["ac_temp"],
                    "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
                }

                # Publish to room-specific topic with retain=True
                pub_topic = f"hvac/room/{room_id}/sensors"
                client.publish(pub_topic, json.dumps(sensor_data), retain=True)
                print(f"\r📤 Sent {room_id}: {sensor_data['temperature']}°C, Occ={sensor_data['occupancy']}", end=" ")
                time.sleep(1) # Small gap between rooms

            time.sleep(2) # Overall update cycle

    except KeyboardInterrupt:
        print("\n👋 Stopping Simulator...")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    run_simulator()
