# my_first_game_Shoot_Aliens
Vertical shooter built with Python + pygame. Current build includes player movement, bullets with cooldown (rapid-fire powerup), scaling enemy waves, collisions, score, lives, powerups, pause, restartable game over screen, and a scrolling starfield background.

## Run
```bash
python3 shoot_aliens_py/day0.py
```

## Configure
Tunable parameters live in `config.json`:
- Core: window size/FPS, player speed & lives, bullet cooldowns, enemy spawn & speed scaling, powerup drop chance, colors, background layers/star density.
- Assets: under `"assets"` you can swap sprites without code changes:
	```json
	"assets": {
		"player": "res/airplane.png",
		"bullet": "res/bullet.png",
		"flash": "res/flash/MuzzleFlash.png",
		"explosion": "res/explosion/exp2_0.png",
		"enemies": ["res/alien.png", "res/alien1.png", "res/alien2.png", "res/alien3.png"]
	}
	```
Use relative paths (from project root) or absolute paths. Edit and rerun; missing keys fall back to defaults.

Architecture: the main game loop is in `shoot_aliens_py/game.py` (Game class). `shoot_aliens_py/day0.py` is a thin entry point that just runs the Game.

## Controls
- Arrow keys: move (up/down/left/right)
- Space or **F**: fire
- P: pause/resume
- R: restart after game over
- Q or Esc: quit from game over screen

## Gameplay notes
- Stages scale automatically as score increases (faster spawns, tougher enemies).
- Powerups can drop from enemies:
	- Green: +1 life (up to max 5)
	- Yellow: Rapid fire for a few seconds