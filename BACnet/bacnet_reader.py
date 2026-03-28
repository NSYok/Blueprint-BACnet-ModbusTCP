import BAC0
import asyncio

# =====================================================================
# Blueprint: Standard BACnet Reader (Direct & Name-based)
# เหมาะสำหรับ: อุปกรณ์ BACnet/IP ทั่วไป (Chiller, Controller, AHU)
# =====================================================================

async def read_direct(client, target_ip, obj_type, obj_instance):
    """
    ฟังก์ชันสำหรับอ่านค่าจากอุปกรณ์โดยระบุตำแหน่ง (Direct Addressing)
    """
    try:
        value = await client.read(f"{target_ip} {obj_type} {obj_instance} presentValue")
        name = await client.read(f"{target_ip} {obj_type} {obj_instance} objectName")
        print(f"✅ Success -> [{name}] Current Value: {value}")
        return value, name
    except Exception as e:
        print(f"❌ Direct read failed: {e}")
        return None, None

async def read_by_name(client, target_ip, object_name):
    """
    ฟังก์ชันสำหรับค้นหาและอ่านค่าผ่าน Object Name
    """
    try:
        # ค้นหาหมายเลขอุปกรณ์ (Device ID)
        devices = await client.who_is(target_ip)
        device_id = None
        
        if devices:
            for dev in devices:
                ip_target = target_ip.split(':')[0] if ':' in target_ip else target_ip
                if ip_target in str(getattr(dev, 'pduSource', '')):
                    ident = getattr(dev, 'iAmDeviceIdentifier', None)
                    if ident and len(ident) > 1:
                        device_id = ident[1]
                    break
        
        if not device_id:
            print(f"❌ Device ID not found on {target_ip}")
            return None
        
        # ดึงรายชื่อพอร์ตทั้งหมดและ Map ตำแหน่ง
        device = await BAC0.device(target_ip, device_id, client)
        available_points = list(device.points_name)

        if object_name in available_points:
            pt = device[object_name]
            obj_type = pt.properties.type
            obj_inst = pt.properties.address
            
            # สั่งอ่านค่าปัจจุบัน (Live data) เพื่อเลี่ยง Cache
            point_val = await client.read(f"{target_ip} {obj_type} {obj_inst} presentValue")
            print(f"✅ Success -> [{object_name}] ({obj_type} {obj_inst}): {point_val}")
            return point_val
        else:
            print(f"❌ Object '{object_name}' not found.")
            return None

    except Exception as e:
        print(f"❌ Name Mapping failed: {e}")
        return None

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

async def run_bacnet_client():
    # --- Configuration ---
    TARGET_IP = "192.168.1.34:47808"
    OBJECT_NAME = "Room_Temp"
    LOCAL_IP = "192.168.1.34"
    LOCAL_PORT = 47811

    print(f"--- BACnet Standard Protocol Starting ---")
    print(f"Target: {TARGET_IP} | Local: {LOCAL_IP}:{LOCAL_PORT}\n")
    
    # ลดข้อความ Log ของระบบไลบรารี BAC0 ที่ไม่จำเป็น
    # BAC0.log_level('error')

    try:
        client = BAC0.lite(ip=LOCAL_IP, port=LOCAL_PORT)
        await asyncio.sleep(1)
        
        print("[Method 1] Direct Addressing...")
        await read_direct(client, TARGET_IP, "analogInput", 1)

        print("-" * 40)

        print("[Method 2] Search by Object Name...")
        await read_by_name(client, TARGET_IP, OBJECT_NAME)

        print("-" * 40)

        print("[Method 3] Writing Value...")
        await write_value(client, TARGET_IP, "analogValue", 1, 25.5)

    except Exception as e:
        print(f"Critical System Error: {e}")
    finally:
        if 'client' in locals():
            client.disconnect()
            print("\n--- Connection Closed ---")

if __name__ == "__main__":
    try:
        asyncio.run(run_bacnet_client())
    except KeyboardInterrupt:
        print("\nStopped by user.")
