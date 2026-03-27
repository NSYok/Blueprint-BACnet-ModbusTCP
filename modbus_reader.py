from pymodbus.client import ModbusTcpClient
import time

# =====================================================================
# Blueprint: Modbus TCP Reader & Writer
# เหมาะสำหรับ: PLC, Sensor, Inverter หรืออุปกรณ์ที่ใช้ Modbus TCP
# =====================================================================

def read_modbus_data():
    # --- ตั้งค่าการเชื่อมต่อ (Configuration) ---
    SERVER_IP = '192.168.1.37'  # ไอพีของอุปกรณ์ Modbus
    SERVER_PORT = 5020         # พอร์ต (มาตรฐานคือ 502)
    UNIT_ID = 1                # Slave ID หรือ Unit Identifier
    
    # สร้าง Modbus TCP Client
    client = ModbusTcpClient(SERVER_IP, port=SERVER_PORT)

    print(f"Connecting to Modbus Server at {SERVER_IP}:{SERVER_PORT}...")

    try:
        # พยายามเชื่อมต่อ
        if client.connect():
            print("Successfully connected!\n")
            
            loop_count = 0
            while True:
                # 1. อ่านค่า Holding Registers
                # address: ตำแหน่งเริ่มต้น (0-based)
                # count: จำนวน register ที่ต้องการอ่าน (เช่น 5 ตัว)
                # device_id: ระบุ Unit ID ของอุปกรณ์
                response = client.read_holding_registers(address=0, count=5, device_id=UNIT_ID)

                if not response.isError():
                    # ดึงค่าออกมาเป็น List [reg0, reg1, reg2, ...]
                    current_values = response.registers
                    print(f"Read Success: {current_values}")
                    
                    # ตัวอย่างการประมวลผล: นำค่าที่อ่านได้มาบวกเพิ่ม 1
                    new_values = [val + 1 for val in current_values]
                    
                    # 2. ลองเขียนค่าใหม่กลับเข้าไปที่อุปกรณ์ (Writeback)
                    try:
                        loop_count += 1
                        print(f"Loop {loop_count} - Writing new values: {new_values}")
                        
                        # ใช้ฟังก์ชัน write_registers เพื่อเขียนค่าแบบ Multiple Registers
                        write_resp = client.write_registers(address=0, values=new_values, device_id=UNIT_ID)
                        
                        if write_resp.isError():
                            print(f"Write Failed: {write_resp}")
                            
                    except Exception as e:
                        print(f"Write Exception: {e}")
                        
                else:
                    print(f"Read Error: {response}")

                print("-" * 40)
                time.sleep(2)  # หน่วงเวลา 2 วินาทีก่อนรอบถัดไป

        else:
            print("Could not connect to Modbus Server. Check IP/Port or Firewall.")

    except Exception as e:
        print(f"System Error: {e}")
    finally:
        client.close()
        print("Connection closed.")

if __name__ == "__main__":
    try:
        read_modbus_data()
    except KeyboardInterrupt:
        print("\nStopped by user.")
