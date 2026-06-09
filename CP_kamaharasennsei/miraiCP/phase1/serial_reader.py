import serial
import threading

COM_RIGHT = 'COM3'  # 9番：右腕
COM_LEFT  = 'COM4'  # 16番：左腕
BAUD_RATE = 115200

latest = {
    'right': {'x': 0, 'y': 0, 'z': 0},
    'left':  {'x': 0, 'y': 0, 'z': 0},
}


def read_serial(port, label):
    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=1)
        print(f"[{label}] {port} 接続OK")
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) == 3:
                try:
                    x, y, z = int(parts[0]), int(parts[1]), int(parts[2])
                    latest[label] = {'x': x, 'y': y, 'z': z}
                    print(f"[{label}] x={x:6d}  y={y:6d}  z={z:6d}")
                except ValueError:
                    pass
    except serial.SerialException as e:
        print(f"[{label}] 接続エラー: {e}")


def start():
    t_right = threading.Thread(target=read_serial, args=(COM_RIGHT, 'right'), daemon=True)
    t_left  = threading.Thread(target=read_serial, args=(COM_LEFT,  'left'),  daemon=True)
    t_right.start()
    t_left.start()
    print("両腕の読み取り開始。Ctrl+C で終了。")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("終了")


if __name__ == "__main__":
    start()
