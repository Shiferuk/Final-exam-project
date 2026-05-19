# Tiny Swords Game

A 2D real-time strategy game built with Python and Pygame, using the "Tiny Swords" asset pack. Players manage resources, recruit troops, and build structures on a large scrollable world map.

---

## Features

- Large open world (5000×5000 tiles) with smooth camera scrolling
- Resource gathering — collect **Gold** and **Wood** from mines and trees
- Unit management — select and command **Warriors** and **Archers**
- Building system — construct **Houses**, **Towers**, and **Castles** with resource costs
- Animated entities — units, sheep, clouds, and loot drops are fully animated
- Save & Load system — game progress is saved to a JSON file and can be resumed
- Y-sorted rendering — objects are drawn in correct depth order
- Build preview — placement ghost with green/red feedback before confirming

---

## Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.x | Core programming language |
| Pygame | Game loop, rendering, input handling |
| JSON | Save/load game state |

---

## Project Structure

```
project/
├── main.py          # Entry point — game loop
├── game_logic.py    # Game class: state machine, camera, UI, save/load
├── entities.py      # Entity, Unit, Warrior, Archer, Sheep, Tree, GoldMine, Buildings
├── config.py        # Global settings, asset loading, screen setup
├── savegame.json    # Auto-generated save file (created on first save)
└── Tiny Swords/     # Asset folder (sprites, tiles, UI elements)
```

---

## Installation

1. **Clone or download** the repository.

2. **Install Python 3.8+** from [python.org](https://www.python.org/).

3. **Install Pygame:**
   ```bash
   pip install pygame
   ```

4. **Add the asset folder.** Place the `Tiny Swords` and `Tiny Swords (Free Pack)` asset folders in the project root directory. The game will display pink placeholder squares for any missing images, so it still runs without them.

---

## How to Run

```bash
python main.py
```

Use the **Start Menu** to begin a new game or continue a saved session.

---

## Controls

| Input | Action |
|---|---|
| Left-click drag | Box-select units |
| Right-click | Move selected units / cancel build mode |
| Left-click (on enemy/resource) | Order selected units to attack or gather |
| Build buttons (top-right) | Enter building placement mode |
| Left-click (in build mode) | Place building |
| Gear icon (top-right) | Open pause / exit menu |
| Middle-click drag | Scroll the camera |

---

## Screenshots

> *(Add screenshots of gameplay here)*

---

## Team Members

| Name | Role |
|---|---|
| *(Team Member 1)* | Game logic, save system |
| *(Team Member 2)* | Entity classes, AI behaviour |
| *(Team Member 3)* | Asset integration, UI, config |
