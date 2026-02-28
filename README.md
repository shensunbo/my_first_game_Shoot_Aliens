# my_first_game_Shoot_Aliens
Vertical shooter built with Python + pygame. Current build includes player movement, bullets with cooldown (rapid-fire powerup), scaling enemy waves, collisions, score, lives, powerups, pause, and restartable game over screen.

## Run
```bash
python3 shoot_aliens_py/day0.py
```

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