import os
import sys
import time
import json
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# Force UTF-8 for Windows Console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from langchain.tools import tool
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

# ==========================================
# 1. นิยามเครื่องมือ (MQTT Integration)
# ==========================================

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
# Topics will be constructed dynamically: hvac/room/{room_id}/sensors

class RoomInput(BaseModel):
    room_id: str = Field(description="รหัสห้อง เช่น 'RM-401'")

@tool("get_live_hvac_telemetry", args_schema=RoomInput)
def get_live_hvac_telemetry(room_id: str) -> str:
    """ใช้ดึงค่าสถานะเซนเซอร์แบบ Real-time (Temperature, Humidity, Occupancy, CO2) จาก MQTT"""
    print(f"🔍 AI กำลังอ่านค่าจากห้อง: {room_id}...")
    # One-shot subscription to catch the latest message from simulator
    data_received = {"raw": None}
    
    def on_msg(client, userdata, msg):
        data_received["raw"] = msg.payload.decode()
        client.disconnect() # Done

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_msg
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        topic = f"hvac/room/{room_id}/sensors"
        client.subscribe(topic)
        
        # Listen for up to 10 seconds for the latest telemetry
        client.loop_start()
        start_time = time.time()
        while data_received["raw"] is None and time.time() - start_time < 10:
            time.sleep(0.1)
        client.loop_stop()
        
        if data_received["raw"]:
            return data_received["raw"]
        else:
            return json.dumps({"status": "timeout", "message": f"ไม่ได้ยินค่าจากห้อง {room_id} ในขณะนี้"})
            
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

class ControlInput(BaseModel):
    room_id: str = Field(description="รหัสห้อง เช่น 'RM-401'")
    command: str = Field(description="คำสั่งที่ต้องการส่ง: 'OFF', 'ECO', 'ON', 'HEAT'")
    set_temp: float = Field(default=26.0, description="อุณหภูมิที่ต้องการตั้งค่า (เฉพาะโหลดที่เป็นการตั้งค่า)")

@tool("control_ac_mqtt", args_schema=ControlInput)
def control_ac_mqtt(room_id: str, command: str, set_temp: float = 26.0):
    """ใช้ควบคุมแอร์ผ่านระบบ MQTT: 'OFF' เพื่อปิด, 'ECO' เพื่อโหมดประหยัด, 'ON' เพื่อเปิดปกติ"""
    print(f"🎮 AI กำลังส่งคำสั่งควบคุม: {command} ไปยังห้อง {room_id} (Target: {set_temp}°C)")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        payload = {
            "room_id": room_id,
            "command": command,
            "set_temp": set_temp,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        topic = f"hvac/room/{room_id}/actuators"
        client.publish(topic, json.dumps(payload))
        client.disconnect()
        return f"✅ ส่งคำสั่ง {command} ไปยังห้อง {room_id} (อุณหภูมิเป้าหมาย {set_temp}°C) เรียบร้อยแล้ว"
    except Exception as e:
        return f"❌ ไม่สามารถส่งคำสั่งได้: {e}"

# ==========================================
# 2. การตั้งค่า Gemini Agent
# ==========================================

# โหลดค่าจากไฟล์ .env ที่อยู่ในโฟลเดอร์เดียวกัน
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

# ⚠️ ดึงค่า Google API Key และเช็คเพื่อป้องกัน Error
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

def run_agent():
    tools = [get_live_hvac_telemetry, control_ac_mqtt]
    
    # 💡 ใช้โมเดล gemini-2.5-flash หรือที่ใหม่กว่า
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)

    # 💡 กำหนด System Prompt ให้ Agent (กฎการตัดสินใจ)
    system_prompt = (
        "คุณคือ AI ผู้ดูแลอาคารอัจฉริยะแบบ Real-Time "
        "หน้าที่ของคุณคือตรวจสอบค่าจาก MQTT Sensors และตัดสินใจดังนี้: "
        "1. ถ้าไม่มีคนอยู่ (occupancy=0) ให้ปิดแอร์ (OFF) ทันที "
        "2. ถ้ามีคนอยู่ แต่อุณหภูมิต่ำกว่า 25 องศา ให้เข้าโหมดประหยัด (ECO) "
        "3. ถ้า CO2_ppm เกิน 1000 ให้แจ้งเตือนผู้ใช้ด้วย "
        "และตอบสรุปผลเป็นภาษาไทยทุกครั้ง"
    )

    # 💡 ใช้ create_agent ตามมาตรฐานใหม่ของ LangChain
    agent_executor = create_agent(
        model=llm, 
        tools=tools, 
        system_prompt=system_prompt
    )

    print("🚀 เริ่มต้นระบบ AI Monitoring...")
    try:
        # ส่งคำสั่งให้ AI ตรวจสอบสถานะจริงเลย
        response = agent_executor.invoke({
            "messages": [("user", "ช่วยตรวจสอบสถานะของห้อง RM-401, RM-402 และ RM-403 ทั้งหมดเลย และสั่งจัดการตามความเหมาะสมทีนะ")]
        })
        
        # ผลลัพธ์จากการตอบกลับล่าสุด (AIMessage)
        print("\n🤖 AI ตัดสินใจว่า:\n", response["messages"][-1].content)
        
    except Exception as e:
        if "API_KEY" in str(e) or "API key not valid" in str(e):
             print("\n❌ Error: กรุณาใส่ GOOGLE_API_KEY ที่ถูกต้องใน .env ครับ")
        else:
             print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    run_agent()
