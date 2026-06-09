import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# 指の第2関節（PIP）と指先（TIP）のランドマークID
FINGER_TIPS = [8, 12, 16, 20]   # 人差し〜小指の指先
FINGER_PIPS = [6, 10, 14, 18]   # 人差し〜小指の第2関節
THUMB_TIP = 4
THUMB_IP  = 3


def is_grip(hand_landmarks) -> bool:
    """全指が曲がっている（グー）かどうかを判定する"""
    fingers_bent = 0

    # 人差し〜小指：指先が第2関節より手首側にあれば曲がっている
    for tip, pip in zip(FINGER_TIPS, FINGER_PIPS):
        if hand_landmarks.landmark[tip].y > hand_landmarks.landmark[pip].y:
            fingers_bent += 1

    # 親指：指先がIP関節より内側にあれば曲がっている
    if hand_landmarks.landmark[THUMB_TIP].x > hand_landmarks.landmark[THUMB_IP].x:
        fingers_bent += 1

    return fingers_bent >= 4


def run():
    cap = cv2.VideoCapture(0)
    prev_grip = False

    with mp_hands.Hands(
        max_num_hands=2,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.7
    ) as hands:

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = hands.process(rgb)

            grip_detected = False

            if result.multi_hand_landmarks:
                for hand_landmarks, handedness in zip(
                    result.multi_hand_landmarks,
                    result.multi_handedness
                ):
                    mp_drawing.draw_landmarks(
                        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS
                    )

                    label = handedness.classification[0].label
                    grip = is_grip(hand_landmarks)

                    if grip:
                        grip_detected = True

                    # 画面にグリップ状態を表示
                    color = (0, 0, 255) if grip else (0, 255, 0)
                    status = "GRIP ON" if grip else "open"
                    wrist = hand_landmarks.landmark[0]
                    cx = int(wrist.x * frame.shape[1])
                    cy = int(wrist.y * frame.shape[0])
                    cv2.putText(frame, f"{label}: {status}", (cx, cy - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # グリップ状態が変わったときだけコンソールに出力
            if grip_detected != prev_grip:
                print("GRIP ON" if grip_detected else "GRIP OFF")
                prev_grip = grip_detected

            cv2.imshow("Gesture Engine - G5 Grip", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
