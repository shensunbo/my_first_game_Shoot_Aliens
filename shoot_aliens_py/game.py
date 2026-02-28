"""Main game loop and state container for Shoot Aliens."""

import random
import sys
from pathlib import Path

import pygame

from airplane import Airplane
from bullet import Bullet
from enemy import Enemy
from powerup import PowerUp, random_powerup_kind
from background import Starfield
from config import load_config


class Game:
    """Encapsulates all gameplay state, rendering, and event handling."""

    def __init__(self, config_path: Path | None = None):
        """Initialize pygame, load config, prepare assets and starting state."""
        pygame.init()

        self.root_dir = Path(__file__).resolve().parent.parent
        self.cfg = load_config(config_path)

        # Extract config values
        w_cfg = self.cfg["window"]
        p_cfg = self.cfg["player"]
        b_cfg = self.cfg["bullet"]
        e_cfg = self.cfg["enemy"]
        c_cfg = self.cfg["colors"]
        pow_cfg = self.cfg["powerups"]

        self.WINDOW_WIDTH = w_cfg["width"]
        self.WINDOW_HEIGHT = w_cfg["height"]
        self.FPS = w_cfg["fps"]
        self.AIRPLANE_SPEED = p_cfg["speed"]
        self.PLAYER_LIVES = p_cfg["lives"]
        self.MAX_LIVES = p_cfg["max_lives"]

        self.BASE_BULLET_COOLDOWN_MS = b_cfg["cooldown_ms"]
        self.RAPID_FIRE_COOLDOWN_MS = b_cfg["rapid_fire_cooldown_ms"]
        self.RAPID_FIRE_DURATION_MS = b_cfg["rapid_fire_duration_ms"]

        self.BASE_SPAWN_MS = e_cfg["base_spawn_ms"]
        self.MIN_SPAWN_MS = e_cfg["min_spawn_ms"]
        self.SPAWN_STEP_MS = e_cfg["spawn_step_ms"]
        self.MAX_ENEMIES = e_cfg["max_enemies"]
        self.STAGE_SCORE_STEP = e_cfg["stage_score_step"]
        self.TOUGH = e_cfg["tough"]
        self.REGULAR = e_cfg["regular"]

        self.POWERUP_DROP_CHANCE = pow_cfg["drop_chance"]

        self.BACKGROUND_COLOR = tuple(c_cfg["background"])
        self.TEXT_COLOR = tuple(c_cfg["text"])

        self.enemy_images = [
            str(self.root_dir / "res" / "alien.png"),
            str(self.root_dir / "res" / "alien1.png"),
            str(self.root_dir / "res" / "alien2.png"),
            str(self.root_dir / "res" / "alien3.png"),
        ]

        # Background
        bg_cfg = self.cfg.get("background", {})
        self.background = Starfield(
            self.WINDOW_WIDTH,
            self.WINDOW_HEIGHT,
            layers=bg_cfg.get("layers", 3),
            stars_per_layer=bg_cfg.get("stars_per_layer", 60),
        )

        # Pygame constructs
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Shoot Aliens")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 26)
        self.big_font = pygame.font.Font(None, 56)

        self.ENEMY_SPAWN_EVENT = pygame.USEREVENT + 1

        # Game state
        self.plane = None
        self.bullets = []
        self.enemies = []
        self.powerups = []
        self.score = 0
        self.lives = self.PLAYER_LIVES
        self.last_shot_time = 0
        self.stage = 1
        self.current_cooldown = self.BASE_BULLET_COOLDOWN_MS
        self.rapid_fire_until = 0
        self.game_over = False
        self.paused = False

        self.reset_game()

    # ---------- Setup & reset ----------
    def set_spawn_timer(self):
        """Schedule enemy spawn timer based on current stage/difficulty."""
        interval = max(self.MIN_SPAWN_MS, self.BASE_SPAWN_MS - (self.stage - 1) * self.SPAWN_STEP_MS)
        pygame.time.set_timer(self.ENEMY_SPAWN_EVENT, interval)

    def reset_game(self):
        """Reset player, enemies, powerups, and progression to defaults."""
        self.plane = Airplane(
            str(self.root_dir / "res" / "airplane.png"),
            100,
            100,
            self.WINDOW_WIDTH // 2,
            self.WINDOW_HEIGHT - 120,
            self.AIRPLANE_SPEED,
        )
        self.bullets = []
        self.enemies = []
        self.powerups = []
        self.score = 0
        self.lives = self.PLAYER_LIVES
        self.last_shot_time = 0
        self.stage = 1
        self.current_cooldown = self.BASE_BULLET_COOLDOWN_MS
        self.rapid_fire_until = 0
        self.game_over = False
        self.paused = False
        self.set_spawn_timer()

    # ---------- Spawning ----------
    def spawn_enemy(self):
        """Create a new enemy with stats derived from stage and config."""
        if len(self.enemies) >= self.MAX_ENEMIES:
            return

        tough_chance = min(
            self.TOUGH["chance_base"] + self.TOUGH["chance_per_stage"] * (self.stage - 1),
            self.TOUGH["chance_max"],
        )
        is_tough = random.random() < tough_chance

        image_path = random.choice(self.enemy_images)
        if is_tough:
            width, height = 90, 90
            hp = self.TOUGH["hp"]
            speed = min(
                self.TOUGH["speed_cap"],
                random.randint(self.TOUGH["speed_base_min"], self.TOUGH["speed_base_max"]) + self.stage // self.TOUGH["speed_stage_div"],
            )
            score_value = self.TOUGH["score"]
        else:
            width, height = 70, 70
            hp = self.REGULAR["hp"]
            speed = min(
                self.REGULAR["speed_cap"],
                random.randint(self.REGULAR["speed_base_min"], self.REGULAR["speed_base_max"]) + self.stage // self.REGULAR["speed_stage_div"],
            )
            score_value = self.REGULAR["score"]

        x = random.randint(width, self.WINDOW_WIDTH - width)
        y = -height
        drift = random.choice([-2, -1, 0, 1, 2])
        self.enemies.append(Enemy(image_path, width, height, x, y, speed, drift, hp=hp, score_value=score_value))

    # ---------- HUD ----------
    def draw_hud(self):
        """Render score bar, health bar, stage, weapon, cooldown, and timers."""
        now = pygame.time.get_ticks()

        # HUD surface (fully transparent background)
        hud_height = 150
        hud_surface = pygame.Surface((self.WINDOW_WIDTH, hud_height), pygame.SRCALPHA)

        self._draw_score_bar(hud_surface, (12, 12), width=300, height=12)

        self._draw_health_bar((12, 36), surface=hud_surface)

        stage_text = self.font.render(f"Stage: {self.stage}", True, self.TEXT_COLOR)
        hud_surface.blit(stage_text, (12, 64))

        weapon = "Rapid Fire" if self.rapid_fire_until > now else "Bullet"
        weapon_text = self.font.render(f"Weapon: {weapon}", True, self.TEXT_COLOR)
        cd_text = self.font.render(f"Fire CD: {self.current_cooldown}ms", True, self.TEXT_COLOR)
        hud_surface.blit(weapon_text, (12, 92))
        hud_surface.blit(cd_text, (190, 92))

        if self.rapid_fire_until > now:
            remaining = max(0, self.rapid_fire_until - now) // 1000 + 1
            rf_text = self.font.render(f"Rapid Fire {remaining}s", True, (255, 215, 0))
            hud_surface.blit(rf_text, (380, 92))

        self.screen.blit(hud_surface, (0, 0))

    def _draw_health_bar(self, pos, surface=None):
        """Draw a simple health bar representing remaining lives."""
        x, y = pos
        bar_width = 190
        bar_height = 14
        pct = max(0, min(1, self.lives / self.MAX_LIVES))
        fill_width = int(bar_width * pct)
        surface = surface or self.screen

        # Background
        pygame.draw.rect(surface, (70, 70, 70), (x, y, bar_width, bar_height), border_radius=6)
        # Fill
        pygame.draw.rect(surface, (220, 80, 80), (x, y, fill_width, bar_height), border_radius=6)
        # Border
        pygame.draw.rect(surface, (240, 240, 240), (x, y, bar_width, bar_height), width=2, border_radius=6)

    # No text label; bar-only per request

    def _draw_score_bar(self, surface, pos, width=280, height=12):
        """Show progress toward the next stage as a bar under the score."""
        x, y = pos
        prev_threshold = max(0, (self.stage - 1) * self.STAGE_SCORE_STEP)
        progress_score = max(0, self.score - prev_threshold)
        pct = min(1.0, progress_score / self.STAGE_SCORE_STEP)
        fill_width = int(width * pct)

        pygame.draw.rect(surface, (60, 70, 100), (x, y, width, height), border_radius=6)
        pygame.draw.rect(surface, (90, 180, 255), (x, y, fill_width, height), border_radius=6)
        pygame.draw.rect(surface, (200, 210, 230), (x, y, width, height), width=1, border_radius=6)

    # No text label; bar-only per request

    def draw_pause(self):
        """Render pause overlay with quick controls/help."""
        title = self.big_font.render("Paused", True, self.TEXT_COLOR)
        self.screen.blit(title, title.get_rect(center=(self.WINDOW_WIDTH // 2, self.WINDOW_HEIGHT // 2)))

    def draw_game_over(self):
        """Render game over overlay and final score."""
        title = self.big_font.render("Game Over", True, self.TEXT_COLOR)
        result = self.font.render(f"Final Score: {self.score}", True, self.TEXT_COLOR)
        self.screen.blit(title, title.get_rect(center=(self.WINDOW_WIDTH // 2, self.WINDOW_HEIGHT // 2 - 70)))
        self.screen.blit(result, result.get_rect(center=(self.WINDOW_WIDTH // 2, self.WINDOW_HEIGHT // 2 - 20)))

    # ---------- Game Loop ----------
    def run(self):
        """Main loop: handle input, update state, render frames."""
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == self.ENEMY_SPAWN_EVENT and not self.game_over and not self.paused:
                    self.spawn_enemy()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p and not self.game_over:
                        self.paused = not self.paused
                    if self.game_over:
                        if event.key == pygame.K_r:
                            self.reset_game()
                        if event.key in (pygame.K_q, pygame.K_ESCAPE):
                            pygame.quit()
                            sys.exit()

            keys = pygame.key.get_pressed()

            if not self.game_over and not self.paused:
                now = pygame.time.get_ticks()

                # Rapid fire expiration
                if now > self.rapid_fire_until and self.current_cooldown != self.BASE_BULLET_COOLDOWN_MS:
                    self.current_cooldown = self.BASE_BULLET_COOLDOWN_MS

                # Firing logic with cooldown
                if keys[pygame.K_f] or keys[pygame.K_SPACE]:
                    if now - self.last_shot_time >= self.current_cooldown:
                        bullet = Bullet(self.plane.rect.centerx, self.plane.rect.top)
                        self.bullets.append(bullet)
                        self.last_shot_time = now

                # Move airplane
                self.plane.move(keys, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

                # Move bullets
                for bullet in self.bullets[:]:
                    bullet.move()
                    if bullet.is_off_screen(self.WINDOW_HEIGHT):
                        self.bullets.remove(bullet)

                # Move enemies and handle collisions
                for enemy in self.enemies[:]:
                    enemy.move(self.WINDOW_WIDTH)

                    # Remove off-screen enemies
                    if enemy.is_off_screen(self.WINDOW_WIDTH, self.WINDOW_HEIGHT):
                        self.enemies.remove(enemy)
                        continue

                    # Bullet hits enemy
                    for bullet in self.bullets[:]:
                        if bullet.rect.colliderect(enemy.rect):
                            if bullet in self.bullets:
                                self.bullets.remove(bullet)
                            if enemy.hit(bullet.damage):
                                if enemy in self.enemies:
                                    self.enemies.remove(enemy)
                                self.score += enemy.score_value
                                # Powerup drop
                                if random.random() < self.POWERUP_DROP_CHANCE:
                                    kind = random_powerup_kind()
                                    self.powerups.append(PowerUp(kind, enemy.rect.centerx, enemy.rect.centery))
                            break

                    if enemy not in self.enemies:
                        continue

                    # Enemy hits player
                    if enemy.rect.colliderect(self.plane.rect):
                        if enemy in self.enemies:
                            self.enemies.remove(enemy)
                        self.lives -= 1
                        if self.lives <= 0:
                            self.game_over = True
                        continue

                # Move powerups and collect
                for item in self.powerups[:]:
                    item.move()
                    if item.is_off_screen(self.WINDOW_HEIGHT):
                        self.powerups.remove(item)
                        continue
                    if item.rect.colliderect(self.plane.rect):
                        if item.kind == "heal":
                            self.lives = min(self.MAX_LIVES, self.lives + 1)
                        elif item.kind == "rapid_fire":
                            self.current_cooldown = self.RAPID_FIRE_COOLDOWN_MS
                            self.rapid_fire_until = now + self.RAPID_FIRE_DURATION_MS
                        self.powerups.remove(item)

                # Stage progression
                next_stage_threshold = self.stage * self.STAGE_SCORE_STEP
                if self.score >= next_stage_threshold:
                    self.stage += 1
                    self.set_spawn_timer()

            # Draw everything
            self.screen.fill(self.BACKGROUND_COLOR)
            self.background.update_and_draw(self.screen)
            self.plane.draw(self.screen)

            for bullet in self.bullets:
                bullet.draw(self.screen)

            for enemy in self.enemies:
                enemy.draw(self.screen)

            for item in self.powerups:
                item.draw(self.screen)

            self.draw_hud()

            if self.paused and not self.game_over:
                self.draw_pause()

            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(self.FPS)
