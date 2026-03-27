import BAC0
import asyncio

# =====================================================================
# Blueprint: BACnet Array Indexing Reader (YABE-style Bypass)
# เหมาะสำหรับ: อุปกรณ์ที่ส่งข้อมูลก้อนใหญ่ไม่สำเร็จ (Segmentation Error) 
# หรืออุปกรณ์จำลอง (Simulator) ที่มีบัคในการส่ง Object List
# =====================================================================

TARGET_IP = "192.168.1.37:47809"
DEVICE_ID = 4194302 
LOCAL_IP = "192.168.1.38"
LOCAL_PORT = 47811

async def read_array_method():
    print("--- BACnet Index Scanning Starting (Bypass Mode) ---")
    try:
        client = BAC0.lite(ip=LOCAL_IP, port=LOCAL_PORT)
        await asyncio.sleep(1)

        print(f"1. Reading objectList length (Index 0) from Device {DEVICE_ID}...")
        
        # เทคนิค: ใน BACnet การอ่าน Array Index 0 จะได้ "จำนวนสมาชิกทั้งหมด" ในลิสต์นั้น
        length = await client.read(f"{TARGET_IP} device {DEVICE_ID} objectList 0")
        print(f"Total Objects discovered: {length}")
        
        if not length or length == 0:
            print("Device reported no objects.")
            return

        print("\n2. Individually fetching each object by index...")
        
        # วนลูปอ่านทีละ Index (เริ่มที่ 1 ถึง N) เพื่อเลี่ยงการดึงข้อมูลก้อนใหญ่รวดเดียว
        for i in range(1, int(length) + 1):
            try:
                # อ่านค่า ID ของวัตถุในตำแหน่งที่ i
                obj_id = await client.read(f"{TARGET_IP} device {DEVICE_ID} objectList {i}")
                
                # obj_id จะได้เป็น Tuple เช่น ('analogInput', 0)
                obj_type, obj_inst = obj_id[0], obj_id[1]
                
                # ดึงชื่อเพื่อแสดงผล
                name = await client.read(f"{TARGET_IP} {obj_type} {obj_inst} objectName")
                print(f"[{i:02d}] {obj_type} {obj_inst} -> Name: '{name}'")
                    
            except Exception as loop_e:
                print(f"Index {i} read error: {loop_e}")

    except Exception as e:
        print(f"Array read process failed: {e}")
    finally:
        if 'client' in locals():
            client.disconnect()
            print("\n--- Connection Closed ---")

if __name__ == "__main__":
    asyncio.run(read_array_method())
