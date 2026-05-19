# Project Report — Tiny Swords Game

---

## 1. Problem Statement

The goal of this project was to build a playable 2D real-time strategy game from scratch using Python and Pygame. The challenge was to combine multiple game systems — rendering, input handling, game state management, entity behaviour, and data persistence — into a single cohesive application without using a high-level game engine.

---

## 2. Solution Overview

We developed a top-down RTS game inspired by classic strategy games. The player controls a small army on a large scrollable map, gathers resources (Gold and Wood), recruits troops, and constructs buildings. The game is built around a state machine with three states: `START_MENU`, `PLAY`, and implicit sub-states (settings panel, build mode).

The codebase is split into four modules with clear responsibilities:

- **`main.py`** — starts the game loop, calls update and draw each frame at 60 FPS.
- **`config.py`** — centralises all constants, screen settings, and asset loading. A `safe_load_image()` helper ensures the game runs even when asset files are missing.
- **`entities.py`** — defines all game objects. `Entity` is the base class; `Unit` adds movement and animation; `Warrior`, `Archer`, `Sheep`, `Tree`, `GoldMine`, `House`, `Tower`, and `Castle` extend these with specific behaviour.
- **`game_logic.py`** — the main `Game` class handles the event loop, camera scrolling, unit selection, build mode, loot spawning, Y-sorted rendering, resource UI, and JSON-based save/load.

---

## 3. System Design

```
main.py
  └── Game (game_logic.py)
        ├── handle_events()   ← keyboard / mouse input
        ├── update()          ← move units, animate, collect loot
        ├── draw()            ← tile map, entities (Y-sorted), UI
        └── _save() / _load_save()  ← JSON persistence
              └── entities.py
                    ├── Entity → Tree, GoldMine, Building
                    └── Unit   → Warrior, Archer, Sheep
                          (uses config.py for images & constants)
```

Key design decisions:
- **Y-sorting** — all renderable objects are sorted by their bottom edge before drawing, creating a convincing depth illusion without a true 3D engine.
- **Camera system** — the camera offset (`camera_x`, `camera_y`) is subtracted at draw time, keeping world coordinates separate from screen coordinates.
- **Build preview** — when build mode is active, a translucent ghost image follows the cursor and turns red when placement is blocked, giving clear visual feedback.

---

## 4. Challenges Faced

**Asset management.** The Tiny Swords asset pack has a complex directory structure with inconsistent naming. We wrote `safe_load_image()` to catch missing files gracefully and continue running with placeholder surfaces, which sped up development significantly.

**Entity interaction and collision.** Making units avoid each other while walking toward a target required checking collisions against all other objects and reverting to the previous position when a collision was detected. Tuning this to feel natural without units getting stuck took several iterations.

**Save and load compatibility.** As the save format evolved during development, old save files would crash on load. We added a compatibility check that falls back to default values if expected keys are missing.

**Performance with many entities.** With 70 trees, 12 mines, 80 decorations, multiple units, and 8 clouds all updating and drawing each frame, early builds dropped below 60 FPS. We resolved this by reducing per-frame work in animation updates and limiting loot spawn object lifetime.

---

## 5. Team Contributions

| Team Member | Contributions |
|---|---|
| *(Member 1)* | `game_logic.py` — event handling, camera, build system, save/load |
| *(Member 2)* | `entities.py` — unit AI, animation, attack and gather behaviour |
| *(Member 3)* | `config.py` — asset pipeline, UI layout, screen configuration |

---

*Submitted as part of the course project. All game assets are from the Tiny Swords asset pack by Pixel Frog.*
