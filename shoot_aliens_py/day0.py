"""Vertical shooter step 3: config-driven tuning for difficulty, powerups, UI."""

import json
import random
import sys
from pathlib import Path

import pygame

from airplane import Airplane
from bullet import Bullet
from enemy import Enemy
from powerup import PowerUp, random_powerup_kind

# Initialize pygame
pygame.init()


DEFAULT_CONFIG = {
    "window": {"width": 1280, "height": 720, "fps": 60},
    "player": {"speed": 8, "lives": 3, "max_lives": 5},
    "bullet": {
        "cooldown_ms": 200,
        "rapid_fire_cooldown_ms": 100,
        "rapid_fire_duration_ms": 5000,
    },
    "enemy": {
        "base_spawn_ms": 750,
        "min_spawn_ms": 250,
        "spawn_step_ms": 40,
        "max_enemies": 14,
        "stage_score_step": 150,
        "tough": {
            "chance_base": 0.15,
            "chance_per_stage": 0.02,
            "chance_max": 0.45,
            "speed_base_min": 3,
            "speed_base_max": 5,
            "speed_stage_div": 3,
            "speed_cap": 9,
            "hp": 3,
            "score": 25,
        },
        "regular": {
            "speed_base_min": 2,
            "speed_base_max": 4,
            "speed_stage_div": 4,
            "speed_cap": 7,
            "hp": 1,
            "score": 10,
        },
    },
    "powerups": {"drop_chance": 0.12, "heal_max_lives": 5},
    "colors": {"background": [5, 5, 20], "text": [240, 240, 240]},
}


def deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load_config(path: Path) -> dict:
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            user_cfg = json.load(f)
        return deep_merge(DEFAULT_CONFIG, user_cfg)
    return DEFAULT_CONFIG


CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"
CFG = load_config(CONFIG_PATH)


# Constants from config
WINDOW_WIDTH = CFG["window"]["width"]
WINDOW_HEIGHT = CFG["window"]["height"]
FPS = CFG["window"]["fps"]
AIRPLANE_SPEED = CFG["player"]["speed"]
BASE_BULLET_COOLDOWN_MS = CFG["bullet"]["cooldown_ms"]
RAPID_FIRE_COOLDOWN_MS = CFG["bullet"]["rapid_fire_cooldown_ms"]
RAPID_FIRE_DURATION_MS = CFG["bullet"]["rapid_fire_duration_ms"]
BASE_SPAWN_MS = CFG["enemy"]["base_spawn_ms"]
MIN_SPAWN_MS = CFG["enemy"]["min_spawn_ms"]
SPAWN_STEP_MS = CFG["enemy"]["spawn_step_ms"]
MAX_ENEMIES = CFG["enemy"]["max_enemies"]
PLAYER_LIVES = CFG["player"]["lives"]
MAX_LIVES = CFG["player"]["max_lives"]
STAGE_SCORE_STEP = CFG["enemy"]["stage_score_step"]
POWERUP_DROP_CHANCE = CFG["powerups"]["drop_chance"]

TOUGH = CFG["enemy"]["tough"]
REGULAR = CFG["enemy"]["regular"]

ENEMY_IMAGES = [
    "res/alien.png",
    "res/alien1.png",
    "res/alien2.png",
    "res/alien3.png",
]

BACKGROUND_COLOR = tuple(CFG["colors"]["background"])
TEXT_COLOR = tuple(CFG["colors"]["text"])

# Initialize screen
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Shoot Aliens")

# Clock and font
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)
big_font = pygame.font.Font(None, 72)

ENEMY_SPAWN_EVENT = pygame.USEREVENT + 1


def spawn_enemy(enemies, stage):
    if len(enemies) >= MAX_ENEMIES:
        return

    # Chance to spawn a tougher enemy as stage increases
    tough_chance = min(
        TOUGH["chance_base"] + TOUGH["chance_per_stage"] * (stage - 1), TOUGH["chance_max"]
    )
    is_tough = random.random() < tough_chance

    image_path = random.choice(ENEMY_IMAGES)
    if is_tough:
        width, height = 90, 90
        hp = TOUGH["hp"]
        speed = min(
            TOUGH["speed_cap"],
            random.randint(TOUGH["speed_base_min"], TOUGH["speed_base_max"]) + stage // TOUGH["speed_stage_div"],
        )
        score_value = TOUGH["score"]
    else:
        width, height = 70, 70
        hp = REGULAR["hp"]
        speed = min(
            REGULAR["speed_cap"],
            random.randint(REGULAR["speed_base_min"], REGULAR["speed_base_max"]) + stage // REGULAR["speed_stage_div"],
        )
        score_value = REGULAR["score"]

    x = random.randint(width, WINDOW_WIDTH - width)
    y = -height
    drift = random.choice([-2, -1, 0, 1, 2])
    enemies.append(Enemy(image_path, width, height, x, y, speed, drift, hp=hp, score_value=score_value))


def reset_game():
    plane = Airplane("res/airplane.png", 100, 100, WINDOW_WIDTH // 2, WINDOW_HEIGHT - 120, AIRPLANE_SPEED)
    bullets = []
    enemies = []
    powerups = []
    score = 0
    lives = PLAYER_LIVES
    last_shot_time = 0
    stage = 1
    current_cooldown = BASE_BULLET_COOLDOWN_MS
    rapid_fire_until = 0
    set_spawn_timer(stage)
    return plane, bullets, enemies, powerups, score, lives, last_shot_time, stage, current_cooldown, rapid_fire_until


def set_spawn_timer(stage: int):
    interval = max(MIN_SPAWN_MS, BASE_SPAWN_MS - (stage - 1) * SPAWN_STEP_MS)
    pygame.time.set_timer(ENEMY_SPAWN_EVENT, interval)


def draw_hud(score, lives, stage, current_cooldown, rapid_fire_until):
    now = pygame.time.get_ticks()
    score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
    lives_text = font.render(f"Lives: {lives}", True, TEXT_COLOR)
    stage_text = font.render(f"Stage: {stage}", True, TEXT_COLOR)
    cd_text = font.render(f"Fire CD: {current_cooldown}ms", True, TEXT_COLOR)
    screen.blit(score_text, (15, 15))
    screen.blit(lives_text, (15, 45))
    screen.blit(stage_text, (15, 75))
    screen.blit(cd_text, (15, 105))

    if rapid_fire_until > now:
        remaining = max(0, rapid_fire_until - now) // 1000 + 1
        rf_text = font.render(f"Rapid Fire {remaining}s", True, (255, 215, 0))
        screen.blit(rf_text, (15, 135))


def draw_pause():
    title = big_font.render("Paused", True, TEXT_COLOR)
    prompt = font.render("Press P to resume", True, TEXT_COLOR)
    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)))
    screen.blit(prompt, prompt.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30)))


def draw_game_over(score):
    title = big_font.render("Game Over", True, TEXT_COLOR)
    prompt = font.render("Press R to restart or Q to quit", True, TEXT_COLOR)
    result = font.render(f"Final Score: {score}", True, TEXT_COLOR)
    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40)))
    screen.blit(result, result.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10)))
    screen.blit(prompt, prompt.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60)))


def main():
    plane, bullets, enemies, powerups, score, lives, last_shot_time, stage, current_cooldown, rapid_fire_until = reset_game()
    game_over = False
    paused = False

    while True:
        screen.fill((0, 50, 50))  # Clear screen with black
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == ENEMY_SPAWN_EVENT and not game_over and not paused:
                spawn_enemy(enemies, stage)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p and not game_over:
                    paused = not paused
                if game_over:
                    if event.key == pygame.K_r:
                        plane, bullets, enemies, powerups, score, lives, last_shot_time, stage, current_cooldown, rapid_fire_until = reset_game()
                        game_over = False
                        paused = False
                    if event.key in (pygame.K_q, pygame.K_ESCAPE):
                        pygame.quit()
                        sys.exit()

        keys = pygame.key.get_pressed()

        if not game_over and not paused:
            now = pygame.time.get_ticks()

            # Rapid fire expiration
            if now > rapid_fire_until and current_cooldown != BASE_BULLET_COOLDOWN_MS:
                current_cooldown = BASE_BULLET_COOLDOWN_MS

            # Firing logic with cooldown
            if keys[pygame.K_f] or keys[pygame.K_SPACE]:
                if now - last_shot_time >= current_cooldown:
                    bullet = Bullet(plane.rect.centerx, plane.rect.top)
                    bullets.append(bullet)
                    last_shot_time = now

            # Move airplane
            plane.move(keys, WINDOW_WIDTH, WINDOW_HEIGHT)

            # Move bullets
            for bullet in bullets[:]:
                bullet.move()
                if bullet.is_off_screen(WINDOW_HEIGHT):
                    bullets.remove(bullet)

            # Move enemies and handle collisions
            for enemy in enemies[:]:
                enemy.move(WINDOW_WIDTH)

                # Remove off-screen enemies
                if enemy.is_off_screen(WINDOW_WIDTH, WINDOW_HEIGHT):
                    enemies.remove(enemy)
                    continue

                # Bullet hits enemy
                for bullet in bullets[:]:
                    if bullet.rect.colliderect(enemy.rect):
                        if bullet in bullets:
                            bullets.remove(bullet)
                        if enemy.hit(bullet.damage):
                            if enemy in enemies:
                                enemies.remove(enemy)
                            score += enemy.score_value
                            # Powerup drop
                            if random.random() < POWERUP_DROP_CHANCE:
                                kind = random_powerup_kind()
                                powerups.append(PowerUp(kind, enemy.rect.centerx, enemy.rect.centery))
                        break

                if enemy not in enemies:
                    continue

                # Enemy hits player
                if enemy.rect.colliderect(plane.rect):
                    if enemy in enemies:
                        enemies.remove(enemy)
                    lives -= 1
                    if lives <= 0:
                        game_over = True
                    continue

            # Move powerups and collect
            for item in powerups[:]:
                item.move()
                if item.is_off_screen(WINDOW_HEIGHT):
                    powerups.remove(item)
                    continue
                if item.rect.colliderect(plane.rect):
                    if item.kind == "heal":
                        lives = min(MAX_LIVES, lives + 1)
                    elif item.kind == "rapid_fire":
                        current_cooldown = RAPID_FIRE_COOLDOWN_MS
                        rapid_fire_until = now + RAPID_FIRE_DURATION_MS
                    powerups.remove(item)

            # Stage progression
            next_stage_threshold = stage * STAGE_SCORE_STEP
            if score >= next_stage_threshold:
                stage += 1
                set_spawn_timer(stage)

        # Draw everything
        screen.fill(BACKGROUND_COLOR)
        plane.draw(screen)

        for bullet in bullets:
            bullet.draw(screen)

        for enemy in enemies:
            enemy.draw(screen)

        for item in powerups:
            item.draw(screen)

        draw_hud(score, lives, stage, current_cooldown, rapid_fire_until)

        if paused and not game_over:
            draw_pause()

        if game_over:
            draw_game_over(score)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()