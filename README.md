# Retro Pulse Arcade Hub

An offline-first, high-polish arcade game hub created in **Python 3 & Pygame**, accompanied by a local vanilla **HTML5/CSS3/JavaScript** launcher dashboard.

---

## 1. What the Game Is
Retro Pulse is a responsive arcade platform designed to deliver satisfaction, speed, and replayability. It features three isolated mini-games:

1. **FLASH! (Reaction):** Target shooting where speed and combo multipliers grant exponentially higher scores.
2. **DON'T GET HIT (Dodge):** Fast-paced survival where you steer an agile core through cascading hazards, collecting deflect shields and bullet-time slow-mo.
3. **SPOT IT (Observation):** An active memory challenge where a scene of geometric shapes is shown, followed by a shape morphing in form, size, or color.

---

## 2. Features
- **Zero Internet Required:** Plays entirely offline once installed.
- **Delta-Time Physics:** Framerate-independent movement and animations targeting a silky 60 FPS.
- **Procedural Audio Synthesizer:** Real-time tone synthesis safeguards against missing audio files; the game will never crash due to missing sound files or sound card limitations.
- **Local Persistence:** Settings and record scores saved in `data/settings.json` and `data/high_scores.json`.
- **Juice & Visual Feedback:** Screen shake, radial glows, pop tweens, floating score combat text, and particle fireworks.

---

## 3. Requirements
- Python 3.8+
- Pygame >= 2.5.0
- Modern Web Browser (optional, for viewing the launcher)

---

## 4. Installation

Clone or extract this folder into your desired directory:

```bash
cd game_project