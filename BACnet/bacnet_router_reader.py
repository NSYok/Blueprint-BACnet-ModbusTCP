import BAC0
import asyncio

# =====================================================================
# Blueprint: Advanced BACnet Router/Virtual Reader
# เหมาะสำหรับ: อุปกรณ์ที่ซ่อนอยู่หลัง Router หรือ Simulator
# =====================================================================

async def discover_device(client, target_device_id):
    """
    ฟังก์ชันสำหรับค้นหา Network Address ของอุปกรณ์ที่ซ่อนอยู่หลัง Router
    """
    try:
        # ใช้ networks=True เพื่อกวาดหาข้าม Network/Virtual Router
        client.discover(networks=True)
        await asyncio.sleep(4) 
        
        devices = getattr(client, 'discovered_devices', [])
        for dev in devices:
            if dev[1] == target_device_id:
                # ส่งกลับ Network_Address ของอุปกรณ์นั้น
                return dev[0]
                
        print(f"❌ Device {target_device_id} not found in discovery.")
        return None
    except Exception as e:
        print(f"❌ Discovery process failed: {e}")
        return None

async def read_direct(client, address, obj_type, obj_instance):
    """
    ฟังก์ชันสำหรับอ่านค่าแบบเจาะจงที่อยู่
    """
    try:
        val = await client.read(f"{address} {obj_type} {obj_instance} presentValue")
        print(f"✅ Success -> [{address}] {obj_type} {obj_instance}: {val}")
        return val
    except Exception as e:
        print(f"❌ Direct read failed: {e}")
        return None

async def read_by_name(client, address, device_id, object_name):
    """
    ฟังก์ชันสำหรับค้นหาและอ่านค่าผ่าน Object Name
    """
    try:
        device = await BAC0.device(address, device_id, client)
        available_points = list(device.points_name)
        
        if object_name in available_points:
            pt = device[object_name]
            obj_type = pt.properties.type
            obj_inst = pt.properties.address
            
            # สั่งอ่านค่าปัจจุบันตัวล่าสุดจาก Device ตรงๆ (เพื่อเลี่ยง Cache ช่วงเริ่มต้น)
            point_val = await client.read(f"{address} {obj_type} {obj_inst} presentValue")
            print(f"✅ Success -> [{object_name}] ({obj_type} {obj_inst}): {point_val}")
            return point_val
        else:
            print(f"❌ Object '{object_name}' not found.")
            return None
    except Exception as e:
        print(f"❌ Name mapping failed: {e}")
        return None

async def write_value(client, address, obj_type, obj_instance, value):
    """
    ฟังก์ชันสำหรับการเขียนค่า (Write Command) ไปยังอุปกรณ์ลูก
    """
    try:
        write_target = f"{address} {obj_type} {obj_instance} presentValue {value}"
        # await client.write(write_target)
        print(f"⚠️ (Code Commented) สั่ง Write สำเร็จ: {write_target}")
        return True
    except Exception as e:
        print(f"❌ Write failed: {e}")
        return False

async def run_router_client():
    # --- Configuration ---
    TARGET_DEVICE_ID = 1  
    OBJECT_NAME = "AV 0"
    LOCAL_IP = "192.168.1.34"
    LOCAL_PORT = 47811

    print(f"--- BACnet Router/Virtual Protocol Starting ---")
    print(f"Seeking Device ID: {TARGET_DEVICE_ID} | Local: {LOCAL_IP}:{LOCAL_PORT}\n")

    try:
        client = BAC0.lite(ip=LOCAL_IP, port=LOCAL_PORT)
        await asyncio.sleep(1)

        print("[Step 1] Global Discovery...")
        found_address = await discover_device(client, TARGET_DEVICE_ID)

        if found_address:
            print(f"✅ Found! Device {TARGET_DEVICE_ID} is at: {found_address}\n")
            print("-" * 40)

            print("[Method 1] Direct Read...")
            await read_direct(client, found_address, "analogValue", 0)

            print("-" * 40)

            print("[Method 2] Name Mapping...")
            await read_by_name(client, found_address, TARGET_DEVICE_ID, OBJECT_NAME)

            print("-" * 40)

            print("[Method 3] Writing Value...")
            await write_value(client, found_address, "binaryOutput", 0, 1)
        else:
            print("\nCannot proceed without network address. Skipping reads.")

    except Exception as e:
        print(f"Critical Error: {e}")
    finally:
        if 'client' in locals():
            client.disconnect()
            print("\n--- Connection Closed ---")

if __name__ == "__main__":
    try:
        asyncio.run(run_router_client())
    except KeyboardInterrupt:
        print("\nStopped by user.")
