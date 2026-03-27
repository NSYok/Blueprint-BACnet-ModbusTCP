# LABtest: BACnet & Modbus Data Reader Blueprints

ชุดสคริปต์ Python สำหรับการดึงข้อมูลจากอุปกรณ์ Industrial Protocol (BACnet/IP และ Modbus TCP) โดยเน้นความยืดหยุ่นและการแก้ปัญหาในระดับ Network ต่างๆ

## 📂 รายชื่อไฟล์ในโปรเจกต์

### 1. [bacnet_reader.py](file:///d:/Repo/LABtest/bacnet_reader.py) - ท่ามาตรฐาน (Standard/Direct)
*   **นิยาม:** สคริปต์พื้นฐานสำหรับดึงข้อมูล BACnet โดยใช้วิธีระบุที่อยู่ตรงๆ (Direct Addressing) และการค้นหาด้วยชื่อ (Name Mapping)
*   **เหมาะสำหรับ:** อุปกรณ์ทั่วไปที่ต่อตรงผ่าน IP (เช่น Chiller, Power Meter, AHU)
*   **จุดเด่น:** ใช้งานง่าย รวดเร็ว และรองรับ BAC0 เวอร์ชั่น 2025 (asyncio)

### 2. [bacnet_router_reader.py](file:///d:/Repo/LABtest/bacnet_router_reader.py) - ท่าทะลวง Router (Router/Virtual)
*   **นิยาม:** สคริปต์สำหรับเจาะจงค้นหาอุปกรณ์ที่ซ่อนอยู่หลัง Router หรือเป็นระบบ Virtual Device (เช่น Simulator)
*   **เหมาะสำหรับ:** อุปกรณ์ที่เป็น Gateway (MS/TP to IP) หรือ Simulator ที่มี Device ซ้อนหลายเลเยอร์
*   **จุดเด่น:** ใช้ `client.discover(networks=True)` เพื่อกวาดหาลูกๆ ทั้งหมดใน Subnet อัตโนมัติ

### 3. [bacnet_yabe_bypass.py](file:///d:/Repo/LABtest/bacnet_yabe_bypass.py) - ท่างัดแงะ (Index Scanning)
*   **นิยาม:** สคริปต์ที่เลียนแบบพฤติกรรมของโปรแกรม YABE โดยการอ่านข้อมูลทีละ Index แทนการขอก้อนใหญ่
*   **เหมาะสำหรับ:** อุปกรณ์ที่มีจุดเยอะเกินไปจนหน้างานร่ม (Segmentation Error) หรือ Simulator บางตัวที่ไม่เสถียร
*   **จุดเด่น:** ค่อยๆ อ่านทีละจุด (Array Indexing) ทำให้ดึงข้อมูลได้สำเร็จ 100% แม้อุปกรณ์จะส่งข้อมูลก้อนใหญ่ไม่เป็น

### 4. [modbus_reader.py](file:///d:/Repo/LABtest/modbus_reader.py) - Modbus TCP Client
*   **นิยาม:** สคริปต์สำหรับอ่านและเขียนข้อมูล Modbus TCP โดยใช้ `pymodbus`
*   **เหมาะสำหรับ:** PLC, Inverter, หรือ Sensor ที่รองรับแค่ Modbus TCP
*   **จุดเด่น:** แสดงตัวอย่างการอ่านค่าหลายๆ Register พร้อมกันและการเขียนค่ากลับ (Writeback) ในลูป

---

## 🛠 การติดตั้ง (Installation)
ต้องใช้ Python 3.12+ และติดตั้ง Library ดังนี้:
```powershell
pip install BAC0 pymodbus
```

## 🚀 วิธีใช้งาน (Quick Start)
1.  **ตั้งค่า IP:** แก้ไขค่า `TARGET_IP` และ `LOCAL_IP` ในไฟล์ `.py` แต่ละไฟล์ให้ตรงกับวงเน็ตเวิร์คของคุณ
2.  **รันสคริปต์:**
    ```powershell
    py bacnet_reader.py
    ```

---
> [!IMPORTANT]
> สำหรับ Windows: ควรปิด Firewall หรือเพิ่ม Exception ให้ Port 47808 (BACnet Standard) และ 47811 (Custom Port) เพื่อป้องกันการ Discovery ล้มเหลว
