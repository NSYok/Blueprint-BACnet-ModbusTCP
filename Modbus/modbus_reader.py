from pymodbus.client import ModbusTcpClient
import time

# =====================================================================
# Blueprint: Modbus TCP Reader & Writer
# เหมาะสำหรับ: PLC, Sensor, Inverter หรืออุปกรณ์ที่ใช้ Modbus TCP
# =====================================================================

def read_data(client, address, count, unit_id):
    """
    ฟังก์ชันสำหรับอ่านค่าจาก Holding Registers f03
    """
    try:
        response = client.read_holding_registers(address=address, count=count, slave=unit_id)
        if not response.isError():
            return response.registers
        else:
            print(f"❌ Read Error: {response}")
            return None
    except Exception as e:
        print(f"❌ Read Exception: {e}")
        return None

def write_data(client, address, values, unit_id):
    """
    ฟังก์ชันสำหรับเขียนค่าลงใน Holding Registers f05
    """
    try:
        write_resp = client.write_registers(address=address, values=values, slave=unit_id)
        if not write_resp.isError():
            print(f"✅ Write Success: {values}")
            return True
        else:
            print(f"❌ Write Failed: {write_resp}")
            return False
    except Exception as e:
        print(f"❌ Write Exception: {e}")
        return False

def run_modbus_client():
    # --- ตั้งค่าการเชื่อมต่อ (Configuration) ---
    SERVER_IP = '192.168.1.37'
    SERVER_PORT = 5020
    UNIT_ID = 1
    
    client = ModbusTcpClient(SERVER_IP, port=SERVER_PORT)
    print(f"Connecting to Modbus Server at {SERVER_IP}:{SERVER_PORT}...")

    try:
        if client.connect():
            print("Successfully connected!\n")
            
            loop_count = 0
            while True:
                loop_count += 1
                print(f"--- Loop {loop_count} ---")
                
                # 1. ทดสอบการอ่าน
                # address: ตำแหน่งเริ่มต้น (0-based)
                # count: จำนวน register ที่ต้องการอ่าน
                # device_id: ระบุ Unit ID ของอุปกรณ์
                response = read_data(client, address=0, count=5, unit_id=UNIT_ID)
                
                if response:
                    print(f"Read values: {response}")
                    
                    # 2. ทดสอบการเขียน (ตัวอย่าง: เพิ่มค่าทีละ 1 แล้วเขียนกลับ)
                    new_values = [val + 1 for val in response]
                    write_data(client, address=0, values=new_values, unit_id=UNIT_ID)
                
                print("-" * 40)
                time.sleep(2)

        else:
            print("Could not connect to Modbus Server.")

    except Exception as e:
        print(f"System Error: {e}")
    finally:
        client.close()
        print("Connection closed.")

if __name__ == "__main__":
    try:
        run_modbus_client()
    except KeyboardInterrupt:
        print("\nStopped by user.")
