import os
import sys
import time
import json
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
from langgraph.checkpoint.memory import InMemorySaver

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

class AnswerofAI(BaseModel):
    room: str = Field(description="ห้องที่จัดการ")
    action: str = Field(description="คำสั่งที่ต้องการส่ง เช่น ประกาศ ,สั่งปรับอุณหภูมิ ,ไม่ปรับเปลี่ยน")
    time: str = Field(description="เวลาที่ส่งคำสั่งในรูปแบบ HH:MM:SS")

class FinalBuildingReport(BaseModel):
    reports: list[AnswerofAI] = Field(description="รายการสรุปผลการจัดการของทุกห้อง")
# ==========================================
# 2. การตั้งค่า Gemini Agent
# ==========================================

load_dotenv()
# 🧠 ตั้งค่า Memory (Checkpointer) เพื่อให้ AI จำสิ่งที่ทำไปแล้วได้
checkpointer = InMemorySaver()
config = {"configurable": {"thread_id": "hvac_automation_workshop"}}

def run_agent():
    tools = [get_live_hvac_telemetry, control_ac_mqtt]
    
    # 💡 ใช้โมเดล gemini-2.0-flash (เสถียรกว่า)
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview", temperature=0)

    # 💡 กำหนด System Prompt ให้ Agent (กฎการตัดสินใจ)
    system_prompt = (
        "คุณคือ AI ผู้ดูแลอาคารอัจฉริยะแบบ Real-Time "
        "หน้าที่ของคุณคือตรวจสอบค่าเซนเซอร์จาก MQTT และตัดสินใจดังนี้: "
        "1. หากห้องว่าง (occupancy=0) -> ต้องสั่งปิดแอร์ (OFF) ทันที "
        "2. หากมีคนอยู่ แต่ Temp < 25 -> ต้องสั่งเข้าโหมดประหยัด (ECO) "
        "3. หาก CO2_ppm > 1000 -> ต้องแจ้งเตือนผู้ใช้เรื่องคุณภาพอากาศ "
        "4. กฎเหล็ก: คุณต้องตรวจสอบสถานะ RM-401, RM-402 และ RM-403 และ 'ต้องเรียกใช้ control_ac_mqtt ให้ครบทุกห้อง' ที่จำเป็นตามกฎข้างต้น "
        "ห้ามข้ามห้องเด็ดขาด ทำงานให้เสร็จทุกห้องก่อนจึงจะสรุปผลเป็นภาษาไทยแยกทีละห้องให้ชัดเจน"
        "5. หากไม่จำเป็นต้องปรับเปลี่ยนสถานะของห้องใดๆ ให้ระบุว่า 'ไม่ปรับเปลี่ยน' ในช่อง action"
        "6. ระบุเวลาปัจจุบันทุกครั้งที่ทำงานในรูปแบบ HH:MM:SS"
    )

    # 💡 ใช้ create_agent พร้อมระบบ Checkpointer
    agent_executor = create_agent(
        model=llm, 
        tools=tools, 
        system_prompt=system_prompt,
        checkpointer=checkpointer
    )

    # 💡 กำหนดค่าเริ่มต้นให้ AI (ใช้โครงสร้าง List เพื่อให้รองรับหลายห้อง)
    structured_parser = llm.with_structured_output(FinalBuildingReport)

    print("🚀 เริ่มต้นระบบ AI Monitoring ...")
    try:
        for i in range(1, 5):
            print(f"\n--- 🔄 รอบที่ {i} ---")
            response = agent_executor.invoke({
                "messages": [("user", "ตอนนี้สภาวะของห้อง RM-401, RM-402 และ RM-403 เป็นอย่างไรบ้าง และควรจัดการอย่างไรดี?")]
            }, config=config)
            raw_answer = response["messages"][-1].content
            print(f"\n🤖 AI ตัดสินใจว่า (รอบที่ {i}):\n", raw_answer)
            
            # 3. ใช้ with_structured_output "ตีกรอบ" ข้อความนั้นเป็น Class AnswerofAI
            result = structured_parser.invoke(f"จากข้อมูลนี้ สรุปผลใส่ในรูปแบบที่กำหนด: {raw_answer}")
            
            # 4. แสดงผลแบบ Structured (ใช้ Loop เพื่อแสดงผลทุกห้อง)
            print(f"\n📊 --- สรุปผลลัพธ์รายห้อง ---")
            if result and hasattr(result, "reports"):
                for report in result.reports:
                    print(f"📍 ห้อง: {report.room}")
                    print(f"🛠️ การจัดการ: {report.action}")
                    print(f"⏰ เวลา: {report.time}")
                    print("-" * 20)
            else:
                print("❌ ไม่พบข้อมูลรายงานในรูปแบบที่กำหนด")
            
            if True:
                print(f"\n⏳ กำลังรอ 30 วินาทีก่อนตรวจสอบรอบที่ {i} (เพื่อดูว่า AI จะจำได้หรือไม่)...")
                time.sleep(30)
    except Exception as e:
        if "API_KEY" in str(e) or "API key not valid" in str(e):
             print("\n❌ Error: กรุณาใส่ GOOGLE_API_KEY ที่ถูกต้องใน .env ครับ")
        else:
             print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    run_agent()
