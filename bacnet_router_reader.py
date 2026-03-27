import BAC0
import asyncio

# =====================================================================
# Blueprint: Advanced BACnet Router/Virtual Reader
# เหมาะสำหรับ: อุปกรณ์ที่ซ่อนอยู่หลัง Router หรือ Simulator (เช่น DEV 1 ใน CBMS)
# =====================================================================

TARGET_DEVICE_ID = 1  # Device Instance ID ของอุปกรณ์ลูกที่เราต้องการหา
OBJECT_NAME = "AI 0"
LOCAL_IP = "192.168.1.38"
LOCAL_PORT = 47811

async def read_virtual_device():
    print(f"--- BACnet Discovery starting ---\nSeeking Device ID: {TARGET_DEVICE_ID}\n")
    try:
        # เปิด BAC0 Lite
        client = BAC0.lite(ip=LOCAL_IP, port=LOCAL_PORT)
        await asyncio.sleep(1)

        print(f"1. Scanning network for all devices (Global Discovery)...")
        
        # คดีพิเศษ: ใช้ .discover(networks=True) เพื่อกวาดหาข้าม Network/Virtual Router
        # คำสั่งนี้จะส่ง Who-Is ไปทั่ว และพยายามระบุเส้นทาง (Routing) ไปหาอุปกรณ์ลูก
        client.discover(networks=True)
        await asyncio.sleep(4) 
        
        print("\nAll Discovered Devices:")
        devices = getattr(client, 'discovered_devices', [])
        print(devices)

        # 2. ค้นหา Network Address ของ Device ที่เราต้องการ
        found_address = None
        for dev in devices:
            # dev จะมีรูปแบบเป็น (Network_Address, Device_ID, ...)
            if dev[1] == TARGET_DEVICE_ID:
                found_address = dev[0]
                break
                
        if not found_address:
            print(f"\n❌ Device {TARGET_DEVICE_ID} not found in discovery.")
            print("Troubleshooting:")
            print("- ตรวจสอบว่าเปิดการทำงาน (Start/Run) ของอุปกรณ์ลูกแล้วหรือยัง")
            print("- ตรวจสอบว่า Router อนุญาตให้ Routing ข้อมูลออกภายนอกหรือไม่")
            return
            
        print(f"\n✅ Found! Device {TARGET_DEVICE_ID} is at: {found_address}")
        
        # 3. การดึงข้อมูลแบบ Direct (Direct Addressing)
        print(f"\n[Method 1] Direct Read from {found_address}...")
        try:
            val = await client.read(f"{found_address} analogInput 0 presentValue")
            print(f"✅ Value: {val}")
        except Exception as e:
            print(f"❌ Direct read failed: {e}")

        # 4. การดึงรายชื่อ Points (Name Mapping)
        print(f"\n[Method 2] Name Mapping...")
        try:
            # สร้างตัวแทนอุปกรณ์โดยระบุ Network Address และ Device ID
            device = await BAC0.device(found_address, TARGET_DEVICE_ID, client)
            available_points = list(device.points_name)
            
            if OBJECT_NAME in available_points:
                point_val = device[OBJECT_NAME]
                print(f"✅ {OBJECT_NAME}: {point_val}")
            else:
                print(f"❌ '{OBJECT_NAME}' not found.")
                print(f"Available points: {available_points}")
        except Exception as e:
            print(f"❌ Name mapping failed: {e}")

    except Exception as e:
        print(f"Critical Error: {e}")
    finally:
        if 'client' in locals():
            client.disconnect()
            print("\n--- Connection Closed ---")

if __name__ == "__main__":
    try:
        asyncio.run(read_virtual_device())
    except KeyboardInterrupt:
        pass
