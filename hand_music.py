import cv2
import mediapipe as mp
import pygame
import threading
import time

# Initialize pygame mixer
pygame.mixer.init()

# Load note sounds
note_sounds = {
    1: ("C", pygame.mixer.Sound("F:\\Projects\\OpenCV\\HandMusic\\Processed_Sounds\\C.wav")),
    2: ("Am", pygame.mixer.Sound("F:\\Projects\\OpenCV\\HandMusic\\Processed_Sounds\\Am.wav")),
    3: ("F", pygame.mixer.Sound("F:\\Projects\\OpenCV\\HandMusic\\Processed_Sounds\\F.wav")),
    4: ("G", pygame.mixer.Sound("F:\\Projects\\OpenCV\\HandMusic\\Processed_Sounds\\G.wav")),
    5: ("G", pygame.mixer.Sound("F:\\Projects\\OpenCV\\HandMusic\\Processed_Sounds\\G.wav"))
}

# Setup audio channels
channel_A = pygame.mixer.Channel(1)
channel_B = pygame.mixer.Channel(2)

current_channel = channel_A
fade_channel = channel_B

current_note = ""
last_finger_count = -1
volume = 0.8

# Function to fade in volume
def fade_in(channel, sound, target_volume=0.8, duration=1.0):
    steps = 20
    delay = duration / steps
    channel.set_volume(0.0)
    channel.play(sound)
    for i in range(1, steps + 1):
        vol = (i / steps) * target_volume
        channel.set_volume(vol)
        time.sleep(delay)

# Initialize webcam
cap = cv2.VideoCapture(0)

# Mediapipe hands
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands()

# Function to count raised fingers
def count_fingers(hand):
    fingers = []
    if hand.landmark[4].x < hand.landmark[3].x:
        fingers.append(1)
    else:
        fingers.append(0)
    tips = [8, 12, 16, 20]
    for tip in tips:
        if hand.landmark[tip].y < hand.landmark[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)
    return fingers.count(1)

pending_note = None
pending_note_name = ""

def play_note_after_current(new_sound, new_note_name):
    global current_channel, fade_channel, current_note

    # Wait for the current sound to finish
    while current_channel.get_busy():
        time.sleep(0.1)

    # Fade in new sound
    threading.Thread(target=fade_in, args=(fade_channel, new_sound, volume, 1.0)).start()

    # Swap channels
    current_channel, fade_channel = fade_channel, current_channel
    current_note = new_note_name

while True:
    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    finger_count = 0
    hand_detected = False

    if result.multi_hand_landmarks:
        hand_detected = True
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            finger_count = count_fingers(hand_landmarks)

    # If finger changes and valid
    if hand_detected and finger_count != last_finger_count and finger_count in note_sounds:
        last_finger_count = finger_count
        name, sound = note_sounds[finger_count]

        if current_channel.get_busy():
            current_channel.fadeout(1000)
            threading.Thread(target=play_note_after_current, args=(sound, name)).start()
        else:
            threading.Thread(target=fade_in, args=(current_channel, sound, volume, 1.0)).start()
            current_note = name

    # No hand = fade out
    if not hand_detected and current_channel.get_busy():
        current_channel.fadeout(1000)
        current_note = ""
        last_finger_count = -1

    # Display
    cv2.putText(frame, f'Fingers: {finger_count}', (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    cv2.putText(frame, f'Chord: {current_note}', (10, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 200, 200), 2)
    cv2.putText(frame, '1: C   2: Am   3: F   4/5: G', (10, 440),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 255, 200), 2)

    cv2.imshow("Music Gesture Cam", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break
    elif key == ord('+') or key == ord('='):
        volume = min(1.0, volume + 0.1)
    elif key == ord('-') or key == ord('_'):
        volume = max(0.0, volume - 0.1)

cap.release()
cv2.destroyAllWindows()
