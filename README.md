# Real-Time Hand Gesture Media Controller

A real-time hand gesture recognition system built with **OpenCV** and **MediaPipe** that allows users to control a virtual media player using hand gestures. The application detects hand landmarks, recognizes gestures, and provides visual and audio feedback in real time.

---

## Features

- Real-time hand tracking using MediaPipe  
- Gesture-based media control:
  - STOP  
  - PLAY (START)  
  - PAUSE  
  - OK  
  - PEACE (with animated GIF)  
  - ROCK (special visual effects)  
- Volume control using the distance between thumb and index finger  
- Visual feedback:
  - Progress bar  
  - Volume bar  
  - Gesture detection UI  
- Audio feedback (beeps)  
- Dynamic visual effects (lightning, overlays, animations)  

---

## Technologies Used

- Python  
- OpenCV  
- MediaPipe  
- NumPy  

---

## Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/hand-gesture-player.git
cd hand-gesture-player
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate it

Windows

```bash
venv\Scripts\activate
```
Linux/Mac

```bash
source venv/bin/activate
```

4. Install dependencies

```bash
pip install -r requirements.txt
```

Run the project
```bash
python main.py
```
Press Q to quit the application.


## Gesture Controls

| Gesture              | Action         |
| -------------------- | -------------- |
| Fist                 | STOP           |
| Open hand            | PAUSE          |
| Thumb up             | PLAY           |
| Thumb + Index        | OK             |
| Peace (2 fingers)    | Animation      |
| Rock (index + pinky) | Visual effects |


## Volume Control 

The volume is controlled by the distance between the thumb and index finger:

Fingers close → Low volume

Fingers far apart → High volume


