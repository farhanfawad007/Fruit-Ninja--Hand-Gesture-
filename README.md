# 🥷🍉 Gesture Fruit Ninja

<div align="center">

**Slice flying fruits in real-time using your bare hands and a webcam!**  
*Powered by Python, Pygame, OpenCV, and Google MediaPipe Tasks API.*

<p>
  <img src="https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Pygame-2.5%2B-00C853?style=for-the-badge&logo=python&logoColor=white" alt="Pygame">
  <img src="https://img.shields.io/badge/MediaPipe-Vision_AI-00B0FF?style=for-the-badge&logo=google&logoColor=white" alt="MediaPipe">
  <img src="https://img.shields.io/badge/OpenCV-Computer_Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
</p>

<br>

![Gesture Fruit Ninja - Hand Tracking Preview](Gemini_Generated_Image_jnmu4qjnmu4qjnmu-clean.jpg)

<p><i>Real-time 21-point hand skeletal tracking with Picture-in-Picture (PiP) camera overlay in the bottom-right corner.</i></p>

[✨ Features](#-key-features) • 
[📸 Screenshots](#-game-previews) • 
[🎮 Gameplay & Scoring](#-gameplay--difficulty-modes) • 
[🚀 Installation](#-quick-start--installation) • 
[🛠️ Utilities](#️-built-in-asset--audio-generators) • 
[🔧 Troubleshooting](#-troubleshooting)

</div>

---

## ✨ Key Features

<table>
  <tr>
    <td width="50%">
      <h3>🖐️ AI Hand Gesture Control</h3>
      Uses Google's <b>MediaPipe Hand Landmarker</b> (<code>hand_landmarker.task</code>) to track 21 3D hand joints at 60 FPS. Your index fingertip (<b>Landmark #8</b>) acts as a glowing cyan katana blade!
    </td>
    <td width="50%">
      <h3>📷 Picture-in-Picture (PiP) HUD</h3>
      Features a live, mirrored webcam feed in the <b>bottom-right corner</b> with neon-green skeletal lines, cyan joints, and a red target indicator on your slicing finger.
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🖱️ Smart Hybrid / Mouse Fallback</h3>
      No webcam? No problem! The engine automatically detects missing camera hardware and switches seamlessly to <b>Mouse Fallback Mode</b> so you can still play.
    </td>
    <td width="50%">
      <h3>🎨 Dynamic Juice & Physics Engine</h3>
      Sprites split dynamically into left/right halves upon slicing! Includes permanent juice splatters on the dojo wall, radial particle bursts, screen shake, and synthesized WAV audio.
    </td>
  </tr>
</table>

---

## 📸 Game Previews

<div align="center">
  <table>
    <tr>
      <td align="center" width="50%">
        <b>🖐️ Hand Gesture Camera Mode (Bottom-Right PiP)</b><br><br>
        ![Gesture Camera Overlay](Gemini_Generated_Image_jnmu4qjnmu4qjnmu-clean.jpg)
      </td>
      <td align="center" width="50%">
        <b>🖱️ Mouse Fallback / Clean Screen Mode</b><br><br>
        ![Game Over Clean Screen](image_c80a81.jpg)
      </td>
    </tr>
  </table>
</div>

---

## 🎮 Gameplay & Difficulty Modes

### 🍉 Fruit Values & Splatter Effects
Slice multiple fruits in a single swipe to trigger **Combo Bonuses (`2x`, `3x`, `+Bonus Pts`)**!

| Item | Sprite Name | Base Points | Juice Splatter Color | Effect when Sliced |
| :--- | :---: | :---: | :---: | :--- |
| 🍉 **Watermelon** | `watermelon.png` | **+1 PT** | Crimson Red | Splits in half + Red wall splatter |
| 🍎 **Apple** | `apple.png` | **+1 PT** | Cream / Light Yellow | Splits in half + Cream wall splatter |
| 🍌 **Banana** | `banana.png` | **+1 PT** | Lemon Cream | Splits in half + Yellow wall splatter |
| 🍊 **Orange** | `orange.png` | **+1 PT** | Bright Orange | Splits in half + Orange wall splatter |
| 🍍 **Pineapple** | `pineapple.png` | **+2 PTS** | Golden Yellow | High-value target! +2 Points |
| 💣 **Bomb** | `bomb.png` | **Penalty!** | Fiery Orange Blast | Screen shake + Red flash + Lose Life/Points |

### ⚔️ Difficulty Settings
Hover over or slice the difficulty buttons (`EASY`, `MEDIUM`, `HARD`) on the main menu before slicing the spinning watermelon to start:

| Difficulty | Gravity | Spawn Rate | Bomb Chance | Starting Lives | Bomb Penalty |
| :---: | :---: | :---: | :---: | :---: | :--- |
| 🟢 **Easy** | `0.23` (Slow) | Every `110` frames | `8%` | ❤️❤️❤️ (3) | `-1 Life` & `-10 Points` |
| 🟡 **Medium** | `0.30` (Normal) | Every `85` frames | `18%` | ❤️❤️❤️ (3) | `-1 Life` & `-10 Points` |
| 🔴 **Hard** | `0.40` (Fast) | Every `60` frames | `32%` | ❤️❤️❤️ (3) | 💀 **Instant Game Over!** |

> ⚠️ **Strike System:** Letting an unsliced fruit fall off the bottom of the screen costs **1 Life** (`O` turns into a red `X`). Losing all 3 lives triggers **Game Over**.

---

## 🧠 System Architecture

```mermaid
graph LR
    A[📷 Webcam Feed] -->|OpenCV BGR Frame| B(hand_tracking.py)
    B -->|MediaPipe Tasks API| C{Hand Detected?}
    C -->|Yes: Landmark #8| D[🎯 Index Finger Coords]
    C -->|No / No Camera| E[🖱️ Mouse Cursor Fallback]
    B -->|Draw Neon Skeleton| F[🖼️ Bottom-Right PiP Surface]
    D --> G(game.py - Main Loop)
    E --> G
    F --> G
    G -->|Line-Segment Collision| H[🍉 Slice Fruits / 💣 Bombs]
    H --> I[🔊 Pygame Audio & Particles]
