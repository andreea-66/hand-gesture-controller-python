import cv2
import mediapipe as mp
import time
import winsound
from collections import deque
import random
import numpy as np
import math

#Încărcarea GIF-ului pentru gestul PEACE
peace_gif = cv2.VideoCapture("peace.gif")
peace_frames = []
while True:
    ret, frame = peace_gif.read()
    if not ret:
        break
    peace_frames.append(frame)
peace_gif.release()

peace_frame_index = 0
peace_frame_delay = 0
peace_frame_speed = 4   # mai mare = mai lent (4–8 ideal)

# Funcția pentru afișarea GIF-ului (redimensionează GIF-ul după scale)
def draw_gif(frame, gif_frame, center, scale=0.6):
    h, w = gif_frame.shape[:2]
    h = int(h * scale)
    w = int(w * scale)
    gif_frame = cv2.resize(gif_frame, (w, h))

    x = center[0] - w // 2
    y = center[1] - h // 2

    # verificare limite
    if x < 0 or y < 0 or x + w > frame.shape[1] or y + h > frame.shape[0]:
        return frame

    roi = frame[y:y+h, x:x+w]
    blended = cv2.addWeighted(roi, 0.4, gif_frame, 0.6, 0)
    frame[y:y+h, x:x+w] = blended
    return frame

# Configurarea MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# Inițializare cameră (deschidere + obținere lățimea și înălțimea cadrelor video)
cap = cv2.VideoCapture(0)
frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# PLAYER
player_state = "STOP"     # STOP | PLAY | PAUSE
player_progress = 0.0

last_sound_time = 0

# buffer stabilizare gest (Bufferul ajută să stabilizăm gestul: dacă un gest apare de 4 ori din ultimele 6 frame-uri, îl considerăm valid)
gesture_buffer = deque(maxlen=6)

# Numărarea degetelor
def count_fingers(hand, handedness):
    tips = [4, 8, 12, 16, 20]
    fingers = []

    # deget mare
    if handedness == "Right":
        # deget mare ridicat dacă x_tip > x_joint
        fingers.append(1 if hand.landmark[tips[0]].x > hand.landmark[tips[0]-1].x else 0)
    else:
        # pentru mâna stângă invers
        fingers.append(1 if hand.landmark[tips[0]].x < hand.landmark[tips[0]-1].x else 0)

    # celelalte degete
    # Comparăm y_tip cu y_articulație (ridicat dacă vârful e mai sus)
    for i in range(1,5):
        if hand.landmark[tips[i]].y < hand.landmark[tips[i]-2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers

# Recunoașterea gesturilor
def recognize_gesture(f):
    """
    Detectează gesturi pe baza degetelor ridicate:
    STOP, PAUZA, START, OK, PEACE, ROCK
    """
    # STOP: toate coborâte
    if f == [0,0,0,0,0]:
        return "STOP"

    # PAUZA: toate ridicate
    if f == [1,1,1,1,1]:
        return "PAUZA"

    # START: doar deget mare
    if f == [1,0,0,0,0]:
        return "START"

    # OK: deget mare + index
    if f[0] == 1 and f[1] == 1 and sum(f) == 2:
        return "OK"

    # PEACE: doar index + middle ridicate
    # și varianta în care degetul mare e ridicat
    if f[1] == 1 and f[2] == 1 and f[3] == 0 and f[4] == 0:
        return "PEACE"

    # ROCK: index + pinky ridicate
    # middle și ring jos, deget mare poate fi 0 sau 1
    if f[1] == 1 and f[4] == 1 and f[2] == 0 and f[3] == 0:
        return "ROCK"

    # altfel: numărăm degetele ridicate
    return f"{sum(f)} DEGETE"

# Stabilizarea gestului (se consideră valid doar dacă apare de cel puțin 4 ori consecutiv în buffer)
def stable_gesture(new_gesture):
    gesture_buffer.append(new_gesture)
    if gesture_buffer.count(new_gesture) >= 4:
        return new_gesture
    return "NICIUN GEST"

# Sunete pentru gesturi 
def play_sound(gesture):
    global last_sound_time
    if time.time() - last_sound_time < 1:
        return
    last_sound_time = time.time()

    if gesture == "START":
        winsound.Beep(1200, 200)
    elif gesture == "PAUZA":
        winsound.Beep(800, 300)
    elif gesture == "STOP":
        winsound.Beep(400, 400)
    elif gesture == "OK":
        winsound.Beep(1500, 150)

# Desenarea barei de progres
def draw_progress_bar(frame):
    bar_x = 100
    bar_y = frame_h - 80
    bar_w = frame_w - 200
    bar_h = 20

    cv2.rectangle(frame,
                  (bar_x, bar_y),
                  (bar_x + bar_w, bar_y + bar_h),
                  (80, 80, 80), -1)

    cv2.rectangle(frame,
                  (bar_x, bar_y),
                  (bar_x + int(bar_w * player_progress), bar_y + bar_h),
                  (0, 255, 0), -1)

    cv2.putText(frame,
                f"PLAYER: {player_state}",
                (bar_x, bar_y - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9, (255,255,255), 2)

    return frame

# Desenarea efectelor vizuale pentru gesturi 
def draw_visuals(frame, gesture, fingers):
    overlay = frame.copy()
    h, w = frame.shape[:2]

    # STOP
    if gesture == "STOP":
        cv2.rectangle(overlay, (0,0), (w,h), (0,0,255), -1)
        cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
        play_sound("STOP")

    # PAUZA
    elif gesture == "PAUZA":
        cv2.rectangle(overlay, (0,0), (w,h), (0,255,255), -1)
        cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)
        play_sound("PAUZA")

    # START
    elif gesture == "START":
        cv2.rectangle(overlay, (0,0), (w,h), (0,255,0), -1)
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
        play_sound("START")

    # OK
    elif gesture == "OK":
        center = (w//2, h//2)
        cv2.circle(frame, center, 80, (255,255,0), 5)
        play_sound("OK")

    # PEACE GIF
    elif gesture == "PEACE":
        global peace_frame_index, peace_frame_delay

        cx, cy = w // 2, h // 2

        if len(peace_frames) > 0:
            gif_frame = peace_frames[peace_frame_index]
            frame = draw_gif(frame, gif_frame, (cx, cy), scale=0.8)

            peace_frame_delay += 1
            if peace_frame_delay >= peace_frame_speed:
                peace_frame_delay = 0
                peace_frame_index += 1

            if peace_frame_index >= len(peace_frames):
                peace_frame_index = 0

        play_sound("START")



    # ROCK AND ROLL - ANIMATII
    elif gesture == "ROCK":
        cx, cy = w // 2, h // 2
        t = time.time()

        # FULGERE
        for _ in range(5):
            x1 = random.randint(cx - 200, cx + 200)
            y1 = random.randint(cy - 200, cy + 200)
            x2 = x1 + random.randint(-60, 60)
            y2 = y1 + random.randint(60, 120)
            cv2.line(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)

        # STELE
        for _ in range(30):
            angle = random.uniform(0, 2*math.pi)
            dist = random.randint(40, 160)
            x = int(cx + dist * math.cos(angle))
            y = int(cy + dist * math.sin(angle))
            size = random.randint(2, 4)
            cv2.circle(frame, (x, y), size, (255, 255, 0), -1)

        # FLASH
        overlay = frame.copy()
        cv2.rectangle(overlay, (0,0), (w,h), (255,255,255), -1)
        cv2.addWeighted(overlay, 0.08, frame, 0.92, 0, frame)

        play_sound("OK")



    # UI
    cv2.putText(frame, f"GEST: {gesture}",
                (40, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1.4,
                (255,255,255), 3)

    cv2.putText(frame, f"DEGETE: {sum(fingers)}",
                (40, 120),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1,
                (255,255,255), 2)

    for i, f in enumerate(fingers):
        if f:
            cv2.rectangle(frame,
                          (50 + i*50, h-50),
                          (80 + i*50, h-150),
                          (255,0,255), -1)

    return frame

# Control volum cu distanța dintre degetul mare și index 
def draw_volume_bar(frame, hand):
    # selectare vârful degetului mare și index
    thumb_tip = hand.landmark[4]
    index_tip = hand.landmark[8]

    h, w = frame.shape[:2]

    # convertire coordonate relative -> pixeli
    x_thumb, y_thumb = int(thumb_tip.x * w), int(thumb_tip.y * h)
    x_index, y_index = int(index_tip.x * w), int(index_tip.y * h)

    # distanța verticală dintre degetul mare și index 
    dist = math.hypot(x_index - x_thumb, y_index - y_thumb)

    # distanța la volum 0-1 
    min_dist = 20   # deget aproape = 0%
    max_dist = 200  # deget departe = 100%
    vol = np.clip((dist - min_dist) / (max_dist - min_dist), 0, 1)

    # desenare bara de volum în partea dreaptă
    bar_x = w - 100
    bar_y_top = 100
    bar_y_bottom = h - 100
    bar_h = bar_y_bottom - bar_y_top
    filled_h = int(bar_h * vol)

    # bara goală
    cv2.rectangle(frame, (bar_x, bar_y_top), (bar_x + 30, bar_y_bottom), (50,50,50), -1)
    # bara umplută
    cv2.rectangle(frame, (bar_x, bar_y_bottom - filled_h), (bar_x + 30, bar_y_bottom), (0,255,0), -1)

    # valoare procent
    cv2.putText(frame, f"{int(vol*100)}%", (bar_x-10, bar_y_top - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

    return vol


# LOOP PRINCIPAL
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    fingers = [0,0,0,0,0]
    gesture_raw = "NICIUN GEST"

    if result.multi_hand_landmarks:
        for i, hand in enumerate(result.multi_hand_landmarks):
            mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

            # obținem palma (Left/Right)
            handedness = result.multi_handedness[i].classification[0].label

            # numărăm degetele folosind handedness
            fingers = count_fingers(hand, handedness)

            gesture_raw = recognize_gesture(fingers)
            # volume control
            volume = draw_volume_bar(frame, hand)

    gesture = stable_gesture(gesture_raw)

    # control player
    if gesture == "START":
        player_state = "PLAY"
    elif gesture == "PAUZA":
        player_state = "PAUSE"
    elif gesture == "STOP":
        player_state = "STOP"
        player_progress = 0.0

    if player_state == "PLAY":
        player_progress += 0.002
        if player_progress > 1.0:
            player_progress = 1.0

    # Desenare efecte vizuale și UI (User Interface)
    frame = draw_visuals(frame, gesture, fingers)
    frame = draw_progress_bar(frame)
    cv2.imshow("Hand Gesture Control - PSC", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()