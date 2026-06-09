import bluetooth
from microbit import accelerometer, display, Image, sleep
import struct

ble = bluetooth.BLE()
ble.active(True)

# Nordic UART Service
UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
UART_TX   = (bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_NOTIFY)
UART_RX   = (bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_WRITE)

((tx, rx,),) = ble.gatts_register_services([(UART_UUID, (UART_TX, UART_RX))])

connected = False

def ble_irq(event, data):
    global connected
    if event == 1:
        connected = True
        display.show(Image.YES)
    elif event == 2:
        connected = False
        display.show(Image.NO)
        advertise()

ble.irq(ble_irq)

def advertise():
    name = b'miraiCP-L'
    payload = (
        b'\x02\x01\x06' +
        bytes([len(name) + 1, 0x09]) + name
    )
    ble.gap_advertise(100000, adv_data=payload)
    display.show(Image.ARROW_E)

advertise()

while True:
    if connected:
        x = accelerometer.get_x()
        y = accelerometer.get_y()
        z = accelerometer.get_z()
        data = struct.pack('<3h', x, y, z)
        try:
            ble.gatts_notify(0, tx, data)
        except:
            pass
    sleep(100)
