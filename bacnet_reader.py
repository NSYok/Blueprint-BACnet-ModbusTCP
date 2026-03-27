import BAC0
import asyncio
import sys

# =====================================================================
# Blueprint: Standard BACnet Reader (Direct & Name-based)
# เหมาะสำหรับ: อุปกรณ์ BACnet/IP ทั่วไป (Chiller, Controller, AHU)
# =====================================================================

# ตั้งค่าอุปกรณ์เป้าหมาย (Target) และการเชื่อมต่อ (Local)
TARGET_IP = "192.168.1.37:47809"
OBJECT_NAME = "AI 0"
LOCAL_IP = "192.168.1.38"  # ไอพีของคอมพิวเตอร์ที่รันโค้ดนี้
LOCAL_PORT = 47811         # พอร์ตฝั่งเรา (เลี่ยง 47808 เพื่อไม่ให้ชนกับ BMS อื่น)

async def read_bacnet():
    print(f"--- BACnet Standard Reader Starting ---\nTarget: {TARGET_IP}\nLocal: {LOCAL_IP}:{LOCAL_PORT}\n")
    try:
        # เริ่มการเชื่อมต่อด้วยโหมด Lite (Asyncio)
        client = BAC0.lite(ip=LOCAL_IP, port=LOCAL_PORT)
        await asyncio.sleep(1)
        
        # ---------------------------------------------------------
        # วิธีที่ 1: Direct Addressing (อ่านตรงๆ ด้วยที่อยู่ IP)
        # ---------------------------------------------------------
        print("[Method 1] Direct Addressing...")
        try:
            # สั่งอ่านค่าปัจจุบัน (presentValue) และชื่อวัตถุ (objectName)
            value = await client.read(f"{TARGET_IP} analogInput 0 presentValue")
            name = await client.read(f"{TARGET_IP} analogInput 0 objectName")
            print(f"✅ Success -> Object: {name}, Current Value: {value}")
        except Exception as e:
            print(f"❌ Direct read failed: {e}")
            print("Note: หากเป็น Virtual Device ซ้อนแอดเดรสตรงๆ อาจจะไม่พบวัตถุ")

        print("\n" + "="*40 + "\n")

        # ---------------------------------------------------------
        # วิธีที่ 2: Search by Name (ค้นหาผ่าน Device ID)
        # ---------------------------------------------------------
        print("[Method 2] Search by Object Name...")
        try:
            print(f"1. Sending Who-Is to {TARGET_IP}...")
            devices = await client.who_is(TARGET_IP)
            
            device_id = None
            if devices:
                for dev in devices:
                    # ตรวจสอบ Device ID จากการตอบกลับ (IAm Request)
                    if "192.168.1.37" in str(getattr(dev, 'pduSource', '')):
                        ident = getattr(dev, 'iAmDeviceIdentifier', None)
                        if ident and len(ident) > 1:
                            device_id = ident[1]
                        break
            
            if not device_id:
                print("❌ Device ID not found (Check network or firewall).")
            else:
                print(f"2. Device Found (ID: {device_id}). Mapping points...")
                
                # สร้าง Device Object เพื่อดึงรายชื่อจุด (Points) ทั้งหมดมาเก็บไว้ในหน่วยความจำ
                device = await BAC0.device(TARGET_IP, device_id, client)
                
                # แปลง Generator เป็น List เพื่อให้ใช้งานซ้ำและค้นหาได้หลายรอบ
                available_points = list(device.points_name)

                print("--- Device Points List ---")
                for name in available_points:
                    print(f"- {name} (Address: {device[name]})")

                print(f"\n3. Searching for target name: '{OBJECT_NAME}'...")
                if OBJECT_NAME in available_points:
                    point_val = device[OBJECT_NAME]
                    print(f"✅ Success -> {OBJECT_NAME}: {point_val}")
                else:
                    print(f"❌ Object '{OBJECT_NAME}' not found on this device.")

        except Exception as e:
            print(f"❌ Name Mapping failed: {e}")

    except Exception as e:
        print(f"Critical System Error: {e}")
    finally:
        if 'client' in locals():
            client.disconnect()
            print("\n--- Connection Closed ---")

if __name__ == "__main__":
    try:
        asyncio.run(read_bacnet())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
