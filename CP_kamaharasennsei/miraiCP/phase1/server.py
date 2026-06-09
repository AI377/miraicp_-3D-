import asyncio
import json
import threading
from contextlib import asynccontextmanager

import cv2
import mediapipe as mp
import serial
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

# ── 共有状態 ─────────────────────────────────────────────────
# landmarks: [[x,y,z] * 21] | null
state = {
    "right": {"accel": {"x": 0, "y": 0, "z": 0}, "landmarks": None, "btn_a": 0, "btn_b": 0},
    "left":  {"accel": {"x": 0, "y": 0, "z": 0}, "landmarks": None, "btn_a": 0, "btn_b": 0},
}
_lock = threading.Lock()
_clients: list[WebSocket] = []

# ── シリアル読み取り ─────────────────────────────────────────

def read_serial(port: str, side: str) -> None:
    import time
    while True:  # 切断・エラー時に自動リトライ
        try:
            ser = serial.Serial(port, 115200, timeout=1)
            print(f"[{side}] {port} 接続OK")
            while True:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        x, y, z = int(parts[0]), int(parts[1]), int(parts[2])
                        ba = int(parts[3]) if len(parts) > 3 else 0
                        bb = int(parts[4]) if len(parts) > 4 else 0
                        with _lock:
                            state[side]["accel"] = {"x": x, "y": y, "z": z}
                            state[side]["btn_a"] = ba
                            state[side]["btn_b"] = bb
                    except ValueError:
                        pass
        except Exception as e:
            print(f"[{side}] シリアルエラー: {e} — 3秒後に再試行")
            time.sleep(3)

# ── MediaPipe カメラループ ────────────────────────────────────

def camera_loop() -> None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[camera] カメラが開けません")
        return
    print("[camera] カメラ起動OK")

    mp_hands = mp.solutions.hands
    with mp_hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7,
    ) as hands:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # 鏡像反転してから処理（ユーザー視点と一致させる）
            rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            new_lm: dict[str, list | None] = {"Right": None, "Left": None}
            if result.multi_hand_landmarks:
                for lm_data, handedness in zip(
                    result.multi_hand_landmarks, result.multi_handedness
                ):
                    label = handedness.classification[0].label  # "Right" | "Left"
                    new_lm[label] = [[p.x, p.y, p.z] for p in lm_data.landmark]

            with _lock:
                state["right"]["landmarks"] = new_lm["Right"]
                state["left"]["landmarks"]  = new_lm["Left"]

    cap.release()
    print("[camera] 終了")

# ── WebSocket ブロードキャスト（30Hz）────────────────────────

async def _broadcast() -> None:
    while True:
        await asyncio.sleep(1 / 30)
        with _lock:
            msg = json.dumps(state)
        for ws in list(_clients):
            try:
                await ws.send_text(msg)
            except Exception:
                if ws in _clients:
                    _clients.remove(ws)

# ── FastAPI ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    threading.Thread(target=read_serial, args=("COM3", "right"), daemon=True).start()
    threading.Thread(target=read_serial, args=("COM4", "left"),  daemon=True).start()
    threading.Thread(target=camera_loop, daemon=True).start()
    task = asyncio.create_task(_broadcast())
    yield
    task.cancel()


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    _clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in _clients:
            _clients.remove(websocket)


app.mount("/", StaticFiles(directory="static", html=True), name="static")
