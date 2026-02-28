"""Minimal vertical shooter step 1: player movement, bullets, enemies, scoring, lives."""

import random
import sys
import pygame

from airplane import Airplane
from bullet import Bullet
from enemy import Enemy

# Initialize pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
AIRPLANE_SPEED = 8
BULLET_COOLDOWN_MS = 200
ENEMY_SPAWN_MS = 700
MAX_ENEMIES = 12
PLAYER_LIVES = 3

ENEMY_IMAGES = [
    "res/alien.png",
    "res/alien1.png",
    "res/alien2.png",
    "res/alien3.png",
]

BACKGROUND_COLOR = (5, 5, 20)
TEXT_COLOR = (240, 240, 240)

# Initialize screen
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Shoot Aliens")

# Clock and font
clock = pygame.time.Clock()
font = pygame.font.Font(None, 32)
big_font = pygame.font.Font(None, 72)

ENEMY_SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(ENEMY_SPAWN_EVENT, ENEMY_SPAWN_MS)


def spawn_enemy(enemies):
    if len(enemies) >= MAX_ENEMIES:
        return
    image_path = random.choice(ENEMY_IMAGES)
    width, height = 70, 70
    x = random.randint(width, WINDOW_WIDTH - width)
    y = -height
    speed = random.randint(3, 7)
    drift = random.choice([-2, -1, 0, 1, 2])
    enemies.append(Enemy(image_path, width, height, x, y, speed, drift))


def reset_game():
    plane = Airplane("res/airplane.png", 100, 100, WINDOW_WIDTH // 2, WINDOW_HEIGHT - 120, AIRPLANE_SPEED)
    bullets = []
    enemies = []
    score = 0
    lives = PLAYER_LIVES
    last_shot_time = 0
    return plane, bullets, enemies, score, lives, last_shot_time


def draw_hud(score, lives):
    score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
    lives_text = font.render(f"Lives: {lives}", True, TEXT_COLOR)
    screen.blit(score_text, (15, 15))
    screen.blit(lives_text, (15, 50))


def draw_game_over(score):
    title = big_font.render("Game Over", True, TEXT_COLOR)
    prompt = font.render("Press R to restart or Q to quit", True, TEXT_COLOR)
    result = font.render(f"Final Score: {score}", True, TEXT_COLOR)
    screen.blit(title, title.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40)))
    screen.blit(result, result.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10)))
    screen.blit(prompt, prompt.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60)))


def main():
    plane, bullets, enemies, score, lives, last_shot_time = reset_game()
    game_over = False

    while True:
        screen.fill((0, 50, 50))  # Clear screen with black
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == ENEMY_SPAWN_EVENT and not game_over:
                spawn_enemy(enemies)
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    plane, bullets, enemies, score, lives, last_shot_time = reset_game()
                    game_over = False
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.quit()
                    sys.exit()

        keys = pygame.key.get_pressed()

        if not game_over:
            # Firing logic with cooldown
            if keys[pygame.K_f] or keys[pygame.K_SPACE]:
                now = pygame.time.get_ticks()
                if now - last_shot_time >= BULLET_COOLDOWN_MS:
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
                hit = False
                for bullet in bullets[:]:
                    if bullet.rect.colliderect(enemy.rect):
                        if enemy in enemies:
                            enemies.remove(enemy)
                        if bullet in bullets:
                            bullets.remove(bullet)
                        score += 10
                        hit = True
                        break
                if hit:
                    continue

                # Enemy hits player
                if enemy.rect.colliderect(plane.rect):
                    if enemy in enemies:
                        enemies.remove(enemy)
                    lives -= 1
                    if lives <= 0:
                        game_over = True
                    continue

        # Draw everything
        screen.fill(BACKGROUND_COLOR)
        plane.draw(screen)

        for bullet in bullets:
            bullet.draw(screen)

        for enemy in enemies:
            enemy.draw(screen)

        draw_hud(score, lives)

        if game_over:
            draw_game_over(score)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()