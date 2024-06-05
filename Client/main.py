import network
import urequests as requests
import ujson as json
import time
from machine import Pin, SPI, I2C
from mfrc522 import MFRC522
from ssd1306 import SSD1306_I2C
from env import (DOOR_ID, WLAN_SSID, WLAN_SSID, WLAN_PASS, SERVER_IP, SERVER_PORT)


# Initialize RFID reader
reader = MFRC522(spi_id=0, sck=6, miso=4, mosi=7, cs=5, rst=22)

# Initialize I2C for the OLED display
i2c = I2C(id=0, scl=Pin(1), sda=Pin(0), freq=200000)
oled = None

# Initialize greenLED
greenled = Pin(16, Pin.OUT)
greenled.on()
time.sleep(0.5)
greenled.off()
# Initialize redLED
redled = Pin(21, Pin.OUT)
redled.on()
time.sleep(0.5)
redled.off()


def init_oled():
    global oled
    try:
        oled = SSD1306_I2C(128, 64, i2c)
        oled.fill(0)
        oled.text("Initializing...", 0, 0)
        oled.show()
    except Exception as e:
        print("display error:", e)
        # init_oled()


def display_message(message, ip_address):
    try:
        oled.fill(0)
        oled.text(f"Door ID: {DOOR_ID}", 0, 0)  # Display Door ID at the top
        oled.text("___________________", 0, 3)

        lines = message.split("\n")
        for i, line in enumerate(lines):
            oled.text(line, 0, 20 + i * 10)  # Adjust the y position for each line
        oled.text("__________________", 0, 47)
        oled.text(ip_address, 0, 57)  # Display IP address at the bottom
        oled.show()
    except Exception as e:
        greenled.off()
        redled.off()
        print("display error:", e)
        init_oled()

def test_server_connection(ip_address):
    while True:
        try:
            response = requests.get(f"http://{SERVER_IP}:{SERVER_PORT}/")
            if response.status_code == 200:
                print("Server connection successful")
                #display_message(f"Server Connected\nIP: {ip_address}", ip_address)
                return
            else:
                print("Server connection failed")
                display_message(f"Server Fail\nIP: {ip_address}", ip_address)
        except Exception as e:
            print("Server connection error:", e)
            display_message(f"Server Error\n{e}\nIP: {ip_address}", ip_address)

        # Reconnection loop
        while True:
            try:
                response = requests.get(f"http://{SERVER_IP}:{SERVER_PORT}/")
                if response.status_code == 200:
                    print("Reconnected successfully")
                    display_message(f"Server Reconnected\nIP: {ip_address}", ip_address)
                    time.sleep(1)
                    return
                display_message(f"Reconnecting...\nIP: {ip_address}", ip_address)
                time.sleep(1)
            except Exception as e:
                display_message(f"Reconnect Error\n{e}\nIP: {ip_address}", ip_address)
                time.sleep(5)

# Connect to WiFi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        time.sleep(0.5)
        print("Connecting to WiFi...")
    ip_address = wlan.ifconfig()[0]
    print("Connected to WiFi:", ip_address)
    display_message("WiFi Connected", ip_address)
    test_server_connection(ip_address)
    display_message(f"Server Connected\nIP: {ip_address}", ip_address)
    time.sleep(1)

# Function to send RFID UID to the server
def send_rfid_to_server(rfid_uid):
    try :
        url = f"http://{SERVER_IP}:{SERVER_PORT}/access"
        headers = {"Content-Type": "application/json"}
        data = {"rfid_uid": rfid_uid, "door_id": DOOR_ID}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        #print(response.json())
        return response.json()
    except Exception as e:
        test_server_connection(ip_address = network.WLAN(network.STA_IF).ifconfig()[0])
        return {'access_granted': False}
    
# Main loop to scan RFID tags
def main():
    # Retry mechanism for OLED initialization
    for _ in range(3):
        try:
            init_oled()
            break
        except Exception as e:
            print("OLED init error:", e)
            time.sleep(1)

    connect_wifi(WLAN_SSID, WLAN_PASS)
    ip_address = network.WLAN(network.STA_IF).ifconfig()[0]
    display_message("Scan your tag", ip_address)

    while True:
        (status, tag_type) = reader.request(reader.REQIDL)
        if status == reader.OK:
            (status, uid) = reader.SelectTagSN()
            if status == reader.OK:
                rfid_uid_decimal = "".join([str(i) for i in uid])
                print("RFID UID:", rfid_uid_decimal)
                display_message("Checking...", ip_address)

                response = send_rfid_to_server(rfid_uid_decimal)

                if response.get("access_granted"):
                    user_upn = response.get("upn")
                    print("Access Granted:", user_upn)
                    display_message(f"Access Granted\n{user_upn}", ip_address)
                    # Turn on the LED to indicate door open
                    greenled.on()
                    # Add code here to open the door (e.g., trigger a relay)
                else:
                    print("Access Denied")
                    display_message("Access Denied", ip_address)
                    redled.on()

                time.sleep(2)  # Delay to avoid rapid repeated reads
                greenled.off()
                redled.off()  # Turn off the LED
                display_message("Scan your tag", ip_address)


if __name__ == "__main__":
    main()
