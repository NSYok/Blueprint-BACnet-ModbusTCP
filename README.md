# LABtest: BACnet & Modbus Data Reader Blueprints

ชุดสคริปต์ Python สำหรับการดึงข้อมูลจากอุปกรณ์ Industrial Protocol (BACnet/IP และ Modbus TCP) โดยเน้นความยืดหยุ่นและการแก้ปัญหาในระดับ Network ต่างๆ

## 📂 รายชื่อไฟล์ในโปรเจกต์

### 1. [bacnet_reader.py](file:///c:/Users/UsEr/Desktop/Repository/Blueprint-BACnet-ModbusTCP/bacnet_reader.py) - ท่ามาตรฐาน (Standard/Direct)
*   **นิยาม:** สคริปต์พื้นฐานสำหรับดึงข้อมูล BACnet โดยแยกฟังก์ชัน Read และ Write ชัดเจน
*   **จุดเด่น:** 
    *   `read_direct()`: อ่านแบบระบุตำแหน่งตรงๆ
    *   `read_by_name()`: ค้นหาและอ่านผ่าน Object Name (Mapping)
    *   `write_value()`: ตัวอย่างการเขียนค่าลงใน Objects
*   **เหมาะสำหรับ:** อุปกรณ์ทั่วไปที่ต่อตรงผ่าน IP (เช่น Chiller, Power Meter, AHU)

### 2. [bacnet_router_reader.py](file:///c:/Users/UsEr/Desktop/Repository/Blueprint-BACnet-ModbusTCP/bacnet_router_reader.py) - ท่าทะลวง Router (Router/Virtual)
*   **นิยาม:** สคริปต์สำหรับเจาะจงค้นหาอุปกรณ์ที่ซ่อนอยู่หลัง Router หรือเป็นระบบ Virtual Device
*   **จุดเด่น:** 
    *   `discover_device()`: สแกนหาที่อยู่ในเครือข่ายอัตโนมัติ
    *   เพิ่มฟังก์ชันแยก Read/Write แบบเดียวกับท่ามาตรฐาน
*   **เหมาะสำหรับ:** อุปกรณ์ที่เป็น Gateway (MS/TP to IP) หรือ Simulator ที่มี Device ซ้อนหลายเลเยอร์

### 3. [bacnet_yabe_bypass.py](file:///c:/Users/UsEr/Desktop/Repository/Blueprint-BACnet-ModbusTCP/bacnet_yabe_bypass.py) - ท่างัดแงะ (Index Scanning)
*   **นิยาม:** สคริปต์ที่เลียนแบบพฤติกรรมของโปรแกรม YABE โดยการอ่านข้อมูลทีละ Index
*   **จุดเด่น:** 
    *   `get_total_objects()`: การอ่านจำนวน Object ทั้งหมด
    *   `fetch_objects_by_index()`: ค่อยๆ อ่านทีละจุดเพื่อเลี่ยง Segmentation Error (เลียนแบบ YABE)
    *   รองรับการเขียนค่า (Write) ในรูปแบบ Blueprint
*   **เหมาะสำหรับ:** อุปกรณ์ที่มีจุดเยอะเกินไปจนหน้างานร่ม หรือ Simulator บางตัวที่ไม่เสถียร

### 4. [modbus_reader.py](file:///c:/Users/UsEr/Desktop/Repository/Blueprint-BACnet-ModbusTCP/modbus_reader.py) - Modbus TCP Client
*   **นิยาม:** สคริปต์สำหรับอ่านและเขียนข้อมูล Modbus TCP โดยแยกฟังก์ชัน `read_data()` และ `write_data()`
*   **จุดเด่น:** แยกการประมวลผลข้อมูลออกจากการเชื่อมต่อ (Modular) ทำให้ง่ายต่อการนำไป Reuse
*   **เหมาะสำหรับ:** PLC, Inverter, หรือ Sensor ที่รองรับแค่ Modbus TCP

### 5. [mqtt_reader.py](file:///c:/Users/UsEr/Desktop/Repository/Blueprint-BACnet-ModbusTCP/MQTT/mqtt_reader.py) - MQTT Data Reader & Filter
*   **นิยาม:** สคริปต์สำหรับเชื่อมต่อ MQTT เพื่อดึงข้อมูล (Subscribe) และส่งสถานะกลับ (Publish) ในรูปแบบ JSON
*   **จุดเด่น:** 
    *   **JSON Handling**: รองรับการ Parse JSON Payload และส่งคืนค่าในรูปแบบ Structured JSON
    *   **Data Filtering**: มีตัวอย่างการคัดกรองข้อมูล (เช่น แจ้งสถานะ High เมื่อ Temp > 27°C)
    *   **Modern API**: รองรับ paho-mqtt 2.x+ (Callback API v2)
*   **เหมาะสำหรับ:** อุปกรณ์ IoT, Gateway, หรือการเชื่อมต่อกับ Digital Twin ผ่าน MQTT Broker

---

## 🛠 การติดตั้ง (Installation)
Must use Python 3.12+ and install the following libraries:
```powershell
pip install BAC0 pymodbus paho-mqtt
```

## 🚀 วิธีใช้งาน (Quick Start)
1.  **ตั้งค่า IP:** แก้ไขค่า `TARGET_IP`, `DEVICE_ID` และ `LOCAL_IP` ในไฟล์ `.py` แต่ละไฟล์ให้ตรงกับสภาพแวดล้อมของคุณ
2.  **รันสคริปต์:**
    ```powershell
    py bacnet_reader.py
    ```

---
> [!IMPORTANT]
> สำหรับ Windows: ควรปิด Firewall หรือเพิ่ม Exception ให้ Port 47808 (BACnet Standard) และ 47811 (Custom Port) เพื่อป้องกันการ Discovery ล้มเหลว
