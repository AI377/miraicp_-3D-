import asyncio
import struct
from bleak import BleakScanner, BleakClient

# Nordic UART TX characteristic
UART_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

latest = {}

def notification_handler(label):
    def handler(sender, data):
        if len(data) == 6:
            x, y, z = struct.unpack('<3h', data)
            latest[label] = {'x': x, 'y': y, 'z': z}
            print(f"[{label}] x={x:6d}  y={y:6d}  z={z:6d}")
    return handler


async def connect_device(name, label):
    print(f"[{label}] '{name}' をスキャン中...")
    device = await BleakScanner.find_device_by_name(name, timeout=15)
    if device is None:
        print(f"[{label}] 見つかりませんでした")
        return
    print(f"[{label}] 発見: {device.address}")
    async with BleakClient(device) as client:
        print(f"[{label}] 接続OK")
        await client.start_notify(UART_TX_UUID, notification_handler(label))
        print(f"[{label}] データ受信中... Ctrl+C で終了")
        while True:
            await asyncio.sleep(1)


async def main():
    # 2台を並行して接続
    await asyncio.gather(
        connect_device("miraiCP-R", "right"),
        connect_device("miraiCP-L", "left"),
    )

if __name__ == "__main__":
    asyncio.run(main())
