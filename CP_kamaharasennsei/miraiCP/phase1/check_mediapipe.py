import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

with mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
) as hands:

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 左右反転（鏡像表示）
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)

        if result.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(
                result.multi_hand_landmarks,
                result.multi_handedness
            ):
                # 骨格を描画
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                )

                # 手の左右ラベルを表示
                label = handedness.classification[0].label
                wrist = hand_landmarks.landmark[0]
                cx = int(wrist.x * frame.shape[1])
                cy = int(wrist.y * frame.shape[0])
                cv2.putText(frame, label, (cx, cy - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # コンソールに21点の座標を出力
                print(f"--- {label} ---")
                for i, lm in enumerate(hand_landmarks.landmark):
                    print(f"  [{i:2d}] x={lm.x:.3f}  y={lm.y:.3f}  z={lm.z:.3f}")

        cv2.imshow("MediaPipe Hands", frame)

        # qキーで終了
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
