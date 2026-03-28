import paho.mqtt.client as mqtt
import time
import json

# =====================================================================
# Blueprint: MQTT Basic Reader & Writer (Status reporter)
# เหมาะสำหรับ: IoT Gateway, Sensor Node, หรือการเชื่อมต่อกับ Digital Twin
# =====================================================================

# --- Configuration ---
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
TOPIC_SUB = "prodigitaltwin/test/sensor1"
TOPIC_PUB = "prodigitaltwin/test/sensor1/status"

def on_connect(client, userdata, flags, rc, properties=None):
    """
    ฟังก์ชัน callback เมื่อเชื่อมต่อสำเร็จ (ใช้ API v2)
    """
    # ใน paho-mqtt v2 rc คือ ReasonCode object ที่มี value attribute
    # ถ้า rc เป็น int (v1) จะเทียบ rc == 0
    # ถ้าเป็น object (v2) จะเทียบ rc.is_failure
    try:
        if rc == 0:
            print(f"✅ Connected successfully to {MQTT_BROKER}")
            client.subscribe(TOPIC_SUB)
            print(f"📡 Subscribed to: {TOPIC_SUB}")
        else:
            print(f"❌ Connection failed with code {rc}")
    except AttributeError:
        # กรณีใช้ v1 fallback
        if rc == 0:
            print(f"✅ Connected successfully to {MQTT_BROKER}")
            client.subscribe(TOPIC_SUB)
        else:
            print(f"❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """
    ฟังก์ชัน callback เมื่อได้รับข้อความ
    """
    try:
        # 1. รับค่าและถอดรหัส (Decode)
        raw_payload = msg.payload.decode()
        print(f"📥 Incoming [{msg.topic}]: {raw_payload}")

        # 2. พยายามแปลงเป็น JSON (Parse JSON)
        try:
            data = json.loads(raw_payload)
            is_json = True
            print("🔍 JSON Detected: Data processed successfully")
            
            # --- 🚀 [Filter Example] เช็คค่า Temperature ---
            temp_value = data.get("temperature")
            temp_status = "unknown"
            
            if temp_value is not None:
                if temp_value > 27:
                    temp_status = "High (Alert!)"
                    print(f"⚠️ Alert: High Temperature -> {temp_value}°C")
                else:
                    temp_status = "Normal"
                    print(f"✅ Status: Temperature is within range -> {temp_value}°C")
            # -----------------------------------------------

        except json.JSONDecodeError:
            data = raw_payload
            is_json = False
            temp_status = "N/A"
            temp_value = None
            print("📝 Plain Text Detected: Storing as raw string")

        # 3. เตรียมข้อมูลสำหรับส่งกลับ (Construct Response)
        # response_payload = {
        #     "status": "online",
        #     "device": "MQTT_v1",
        #     "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        #     "data_analysis": {
        #         "temperature": temp_value,
        #         "temp_status": temp_status
        #     },
        #     "received": {
        #         "topic": msg.topic,
        #         "is_json": is_json,
        #         "content": data
        #     },
        #     "ack": True
        # }

        response_payload = {
            "device": "MQTT_v1",
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "temp": temp_value,
            "status": temp_status
        }

        # 4. แปลงข้อมูลส่งกลับเป็น JSON (Serialize JSON)
        print(f"📤 Sent JSON Status to [{TOPIC_PUB}]: {response_payload}")
        client.publish(TOPIC_PUB, json.dumps(response_payload, indent=2))
        print(f"📤 Sent JSON Status to [{TOPIC_PUB}]")

    except Exception as e:
        print(f"❌ Critical Error in Message Handling: {e}")

def run_mqtt_client():
    """
    ฟังก์ชันหลักสำหรับรัน MQTT Client
    """
    print(f"--- MQTT Blueprint Starting ---")
    print(f"Broker: {MQTT_BROKER}:{MQTT_PORT}\n")

    # เลือกใช้ Callback API Version 2 (สำหรับ paho-mqtt 2.x+)
    # เพื่อรองรับ library รุ่นใหม่และลด Deprecation Warning
    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        # Fallback สำหรับ paho-mqtt รุ่นเก่า (< 2.0)
        client = mqtt.Client()
    
    # กำหนด Callback functions
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        # เริ่มต้นการเชื่อมต่อ
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # รัน Loop ตลอดเวลาเพื่อรับ/ส่งข้อมูล
        print("🚀 Client loop starting... (Press Ctrl+C to stop)")
        client.loop_forever()

    except Exception as e:
        print(f"⚠️ Critical Error: {e}")
    finally:
        client.disconnect()
        print("\n--- Connection Closed ---")

if __name__ == "__main__":
    try:
        run_mqtt_client()
    except KeyboardInterrupt:
        print("\nStopped by user.")
