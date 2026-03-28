import paho.mqtt.client as mqtt
import time

# MQTT Configuration
MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_TOPIC_SUB = "prodigitaltwin/test/sensor1"
MQTT_TOPIC_PUB = "prodigitaltwin/test/sensor1/status"

def on_connect(client, userdata, flags, rc):
    """Callback for when the client receives a CONNACK response from the server."""
    if rc == 0:
        print(f"Connected successfully to {MQTT_BROKER}")
        # Subscribing in on_connect() means if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(MQTT_TOPIC_SUB)
        print(f"Subscribed to topic: {MQTT_TOPIC_SUB}")
    else:
        print(f"Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a MQTT message is received."""
    payload = msg.payload.decode()
    print(f"Received message from {msg.topic}: {payload}")
    
    # Writing back (publishing) to the status topic
    status_msg = f"ACK: Received '{payload}' at {time.strftime('%Y-%m-%d %H:%M:%S')}"
    client.publish(MQTT_TOPIC_PUB, status_msg)
    print(f"Published status to {MQTT_TOPIC_PUB}: {status_msg}")

def main():
    # Create an MQTT client instance
    client = mqtt.Client()
    
    # Assign callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        # Connect to the broker
        print(f"Connecting to {MQTT_BROKER}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Blocking call that processes network traffic, dispatches callbacks and
        # handles reconnecting.
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        client.disconnect()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
