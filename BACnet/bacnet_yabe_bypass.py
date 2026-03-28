import BAC0
import asyncio

# =====================================================================
# Blueprint: BACnet Array Indexing Reader (YABE-style Bypass)
# เหมาะสำหรับ: อุปกรณ์ที่ส่งข้อมูลก้อนใหญ่ไม่สำเร็จ (Segmentation Error) 
# หรืออุปกรณ์จำลอง (Simulator) ที่มีบัคในการส่ง Object List
# =====================================================================

async def get_total_objects(client, target_ip, device_id):
    """
    อ่าน Array Index 0 เพื่อหา "จำนวนสมาชิกทั้งหมด" ใน Object List
    """
    try:
        length = await client.read(f"{target_ip} device {device_id} objectList 0")
        if not length or length == 0:
            print("❌ Device reported no objects.")
            return 0
            
        print(f"✅ Total Discovered: {length} Objects")
        return int(length)
    except Exception as e:
        print(f"❌ Failed to read object length: {e}")
        return 0

async def fetch_objects_by_index(client, target_ip, device_id, total_length):
    """
    วนลูปอ่านทีละ Index (เลี่ยง Segmentation Error แบบที่ YABE ทำ)
    """
    for i in range(1, total_length + 1):
        try:
            # ดึง Tuple ของ Object เช่น ('analogInput', 0)
            obj_id = await client.read(f"{target_ip} device {device_id} objectList {i}")
            obj_type, obj_inst = obj_id[0], obj_id[1]
            
            # ดึงชื่อ
            name = await client.read(f"{target_ip} {obj_type} {obj_inst} objectName")
            print(f"[{i:02d}] {obj_type} {obj_inst} -> Name: '{name}'")
        except Exception as loop_e:
            print(f"❌ Index {i} read error: {loop_e}")

async def write_value(client, target_ip, obj_type, obj_instance, value):
    """
    ฟังก์ชันสำหรับการเขียนค่า (Write Command)
    """
    try:
        write_target = f"{target_ip} {obj_type} {obj_instance} presentValue {value}"
        # await client.write(write_target)
        print(f"⚠️ (Code Commented) สั่ง Write สำเร็จ: {write_target}")
        return True
    except Exception as e:
        print(f"❌ Write failed: {e}")
        return False

async def run_yabe_bypass_client():
    # --- Configuration ---
    TARGET_IP = "192.168.1.34:47808"
    DEVICE_ID = 3057100 
    LOCAL_IP = "192.168.1.34"
    LOCAL_PORT = 47811

    print("--- BACnet Index Scanning (YABE Bypass) Starting ---")
    print(f"Target: {TARGET_IP} (Device: {DEVICE_ID}) | Local: {LOCAL_IP}:{LOCAL_PORT}\n")

    # ลดข้อความ Log ของระบบไลบรารี BAC0 ที่ไม่จำเป็นแบบเงียบๆ
    import logging
    logging.getLogger('BAC0').setLevel(logging.ERROR)
    logging.getLogger('bacpypes3').setLevel(logging.ERROR)

    try:
        client = BAC0.lite(ip=LOCAL_IP, port=LOCAL_PORT)
        await asyncio.sleep(1)

        print("[Step 1] Reading ObjectList Length...")
        total_length = await get_total_objects(client, TARGET_IP, DEVICE_ID)

        if total_length > 0:
            print("\n[Step 2] Sequentially Fetching Objects...")
            await fetch_objects_by_index(client, TARGET_IP, DEVICE_ID, total_length)

            print("-" * 40)
            
            print("[Step 3] Write Command Example...")
            await write_value(client, TARGET_IP, "analogValue", 0, 0.0)

    except Exception as e:
        print(f"Critical process failed: {e}")
    finally:
        if 'client' in locals():
            client.disconnect()
            print("\n--- Connection Closed ---")

if __name__ == "__main__":
    try:
        asyncio.run(run_yabe_bypass_client())
    except KeyboardInterrupt:
        print("\nStopped by user.")
