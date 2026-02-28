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


class TimedSpriteEffect:
    """One-shot sprite that disappears after a short lifetime."""

    def __init__(self, surface: pygame.Surface, pos: tuple[int, int], duration_ms: int = 90, anchor: str = "center"):
        self.surface = surface
        self.pos = pos
        self.end_time = pygame.time.get_ticks() + duration_ms
        self.anchor = anchor

    def is_dead(self, now: int) -> bool:
        return now >= self.end_time

    def draw(self, screen: pygame.Surface):
        rect = self.surface.get_rect()
        if self.anchor == "midtop":
            rect.midtop = self.pos
        elif self.anchor == "midbottom":
            rect.midbottom = self.pos
        else:
            rect.center = self.pos
        screen.blit(self.surface, rect)


class AnimatedEffect:
    """Multi-frame animation that advances on a fixed frame duration."""

    def __init__(self, frames: list[pygame.Surface], pos: tuple[int, int], frame_ms: int = 50, anchor: str = "center"):
        self.frames = frames
        self.pos = pos
        self.frame_ms = frame_ms
        self.start_time = pygame.time.get_ticks()
        self.anchor = anchor

    def is_dead(self, now: int) -> bool:
        return self._frame_index(now) >= len(self.frames)

    def _frame_index(self, now: int) -> int:
        elapsed = now - self.start_time
        return max(0, elapsed // self.frame_ms)

    def draw(self, screen: pygame.Surface, now: int):
        idx = self._frame_index(now)
        if idx >= len(self.frames):
            return
        frame = self.frames[idx]
        rect = frame.get_rect()
        if self.anchor == "midtop":
            rect.midtop = self.pos
        else:
            rect.center = self.pos
        screen.blit(frame, rect)


class TrailDot:
    """Small fading circle used for bullet afterimage/trail."""

    def __init__(self, pos: tuple[int, int], radius: int = 6, duration_ms: int = 180):
        self.pos = pos
        self.radius = radius
        self.duration_ms = duration_ms
        self.end_time = pygame.time.get_ticks() + duration_ms
        self.surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.surface, (255, 255, 255, 140), (radius, radius), radius)

    def is_dead(self, now: int) -> bool:
        return now >= self.end_time

    def draw(self, screen: pygame.Surface, now: int):
        remaining = max(0, self.end_time - now)
        alpha = int(140 * (remaining / self.duration_ms))
        if alpha <= 0:
            return
        surf = self.surface.copy()
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=self.pos)
        screen.blit(surf, rect)


class Particle:
    """Procedural particle (e.g., smoke or debris) with fade-out."""

    def __init__(self, pos: tuple[int, int], vel: tuple[float, float], radius: int = 6, duration_ms: int = 400, color=(180, 180, 180, 180)):
        self.x, self.y = pos
        self.vx, self.vy = vel
        self.radius = radius
        self.duration_ms = duration_ms
        self.end_time = pygame.time.get_ticks() + duration_ms
        self.color = color
        self.surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.surface, color, (radius, radius), radius)

    def is_dead(self, now: int) -> bool:
        return now >= self.end_time

    def update(self, dt_ms: int):
        self.x += self.vx * (dt_ms / 1000)
        self.y += self.vy * (dt_ms / 1000)

    def draw(self, screen: pygame.Surface, now: int):
        remaining = max(0, self.end_time - now)
        alpha = int(self.color[3] * (remaining / self.duration_ms))
        if alpha <= 0:
            return
        surf = self.surface.copy()
        surf.set_alpha(alpha)
        rect = surf.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(surf, rect)


class Game:
    """Encapsulates all gameplay state, rendering, and event handling."""

    def __init__(self, config_path: Path | None = None, selected_assets: dict | None = None):
        """Initialize pygame, load config, prepare assets and starting state."""
        pygame.init()

        self.root_dir = Path(__file__).resolve().parent.parent
        self.cfg = load_config(config_path)

        # Allow runtime overrides (e.g., from selection screen)
        if selected_assets:
            asset_keys = {"player", "bullet", "flash", "explosion", "enemies"}
            asset_override = {k: v for k, v in selected_assets.items() if k in asset_keys}
            if asset_override:
                self.cfg.setdefault("assets", {}).update(asset_override)
            bg_override = selected_assets.get("background")
            if bg_override:
                self.cfg.setdefault("background", {}).update(bg_override)

        # Extract config values
        w_cfg = self.cfg["window"]
        p_cfg = self.cfg["player"]
        b_cfg = self.cfg["bullet"]
        e_cfg = self.cfg["enemy"]
        c_cfg = self.cfg["colors"]
        pow_cfg = self.cfg["powerups"]
        a_cfg = self.cfg.get("assets", {})

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

        # Assets
        self.PLAYER_IMAGE_PATH = self._resolve_asset_path(a_cfg.get("player", "res/airplane.png"))
        self.BULLET_IMAGE_PATH = self._resolve_asset_path(a_cfg.get("bullet", "res/bullet.png"))
        self.FLASH_IMAGE_PATH = self._resolve_asset_path(a_cfg.get("flash", "res/flash/MuzzleFlash.png"))
        self.EXPLOSION_IMAGE_PATH = self._resolve_asset_path(a_cfg.get("explosion", "res/explosion/exp2_0.png"))
        enemy_assets = a_cfg.get(
            "enemies",
            [
                "res/alien.png",
                "res/alien1.png",
                "res/alien2.png",
                "res/alien3.png",
            ],
        )
        self.enemy_images = [self._resolve_asset_path(p) for p in enemy_assets]

        self.BACKGROUND_COLOR = tuple(c_cfg["background"])
        self.TEXT_COLOR = tuple(c_cfg["text"])

        # Background config
        bg_cfg = self.cfg.get("background", {})
        self.background_mode = bg_cfg.get("mode", "dynamic")
        self.background_image_path = self._resolve_asset_path(bg_cfg.get("image", "res/background.png"))
        self.background_layers = bg_cfg.get("layers", 3)
        self.background_stars = bg_cfg.get("stars_per_layer", 60)

        # Pygame constructs
        self.screen = pygame.display.set_mode((self.WINDOW_WIDTH, self.WINDOW_HEIGHT))
        pygame.display.set_caption("Shoot Aliens")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 26)
        self.big_font = pygame.font.Font(None, 56)

        self.starfield = None
        self.static_background = None
        self._init_background()

        # Preload bullet sprite once for reuse
        self.bullet_surface = pygame.transform.scale(
            pygame.image.load(self.BULLET_IMAGE_PATH).convert_alpha(), (50, 50)
        )
        self.muzzle_flash_surface = pygame.image.load(self.FLASH_IMAGE_PATH).convert_alpha()
        self.explosion_frames = self._load_explosion_frames(self.EXPLOSION_IMAGE_PATH, scale=1.35)

        self.ENEMY_SPAWN_EVENT = pygame.USEREVENT + 1

        # Game state
        self.plane = None
        self.bullets = []
        self.enemies = []
        self.powerups = []
        self.effects = []
        self.score = 0
        self.lives = self.PLAYER_LIVES
        self.last_shot_time = 0
        self.stage = 1
        self.current_cooldown = self.BASE_BULLET_COOLDOWN_MS
        self.rapid_fire_until = 0
        self.game_over = False
        self.paused = False
        self.last_effect_tick = pygame.time.get_ticks()

        self.reset_game()

    # ---------- Setup & reset ----------
    def _init_background(self):
        if self.background_mode == "static":
            try:
                img = pygame.image.load(self.background_image_path).convert()
                self.static_background = pygame.transform.scale(
                    img, (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
                )
                self.starfield = None
                return
            except pygame.error:
                # Fallback to dynamic if loading fails
                self.background_mode = "dynamic"

        self.starfield = Starfield(
            self.WINDOW_WIDTH,
            self.WINDOW_HEIGHT,
            layers=self.background_layers,
            stars_per_layer=self.background_stars,
        )
        self.static_background = None

    def set_spawn_timer(self):
        """Schedule enemy spawn timer based on current stage/difficulty."""
        interval = max(self.MIN_SPAWN_MS, self.BASE_SPAWN_MS - (self.stage - 1) * self.SPAWN_STEP_MS)
        pygame.time.set_timer(self.ENEMY_SPAWN_EVENT, interval)

    def reset_game(self):
        """Reset player, enemies, powerups, and progression to defaults."""
        self.plane = Airplane(
            self.PLAYER_IMAGE_PATH,
            100,
            100,
            self.WINDOW_WIDTH // 2,
            self.WINDOW_HEIGHT - 120,
            self.AIRPLANE_SPEED,
        )
        self.bullets = []
        self.enemies = []
        self.powerups = []
        self.effects = []
        self.score = 0
        self.lives = self.PLAYER_LIVES
        self.last_shot_time = 0
        self.stage = 1
        self.current_cooldown = self.BASE_BULLET_COOLDOWN_MS
        self.rapid_fire_until = 0
        self.game_over = False
        self.paused = False
        self.last_effect_tick = pygame.time.get_ticks()
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

    def _resolve_asset_path(self, path_str: str) -> str:
        """Return absolute path for an asset, resolving relative to project root."""
        path = Path(path_str)
        if path.is_absolute():
            return str(path)
        return str(self.root_dir / path)

    def _load_explosion_frames(self, sheet_path: str, scale: float = 1.0) -> list[pygame.Surface]:
        """Slice a 4x4 explosion sprite sheet into frames and optionally scale."""
        sheet = pygame.image.load(sheet_path).convert_alpha()
        sheet_w, sheet_h = sheet.get_size()
        cols = 4
        rows = 4
        frame_w = sheet_w // cols
        frame_h = sheet_h // rows
        frames: list[pygame.Surface] = []
        for row in range(rows):
            for col in range(cols):
                rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
                frame = sheet.subsurface(rect).copy()
                if scale != 1.0:
                    frame = pygame.transform.scale(frame, (int(frame_w * scale), int(frame_h * scale)))
                frames.append(frame)
        return frames

    def _spawn_muzzle_flash(self):
        width, height = self.muzzle_flash_surface.get_size()
        scaled = pygame.transform.scale(self.muzzle_flash_surface, (int(width * 0.45), int(height * 0.45)))
        rotated = pygame.transform.rotate(scaled, -90)  # head-left asset -> point upward
        pos = (self.plane.rect.centerx, self.plane.rect.top)
        self.effects.append(TimedSpriteEffect(rotated, pos, duration_ms=90, anchor="midbottom"))
        self._spawn_smoke_burst(pos, count=4, spread=30, speed=80, upward_bias=-40, radius_range=(4, 7), life_ms=260)

    def _spawn_explosion(self, pos: tuple[int, int]):
        if not self.explosion_frames:
            return
        self.effects.append(AnimatedEffect(self.explosion_frames, pos, frame_ms=55, anchor="center"))
        self._spawn_smoke_burst(pos, count=12, spread=90, speed=140, upward_bias=-10, radius_range=(6, 11), life_ms=520)

    def _spawn_trail_dot(self, pos: tuple[int, int]):
        self.effects.append(TrailDot(pos, radius=5, duration_ms=160))

    def _spawn_smoke_burst(
        self,
        pos: tuple[int, int],
        count: int = 8,
        spread: float = 60.0,
        speed: float = 120.0,
        upward_bias: float = -20.0,
        radius_range: tuple[int, int] = (5, 9),
        life_ms: int = 420,
    ):
        for _ in range(count):
            angle = random.uniform(-spread, spread)
            mag = random.uniform(speed * 0.4, speed)
            vx = mag * 0.01 * random.choice([-1, 1]) * random.random()
            vy = upward_bias + random.uniform(-speed * 0.1, speed * 0.2)
            radius = random.randint(radius_range[0], radius_range[1])
            color = (random.randint(150, 200), random.randint(150, 200), random.randint(150, 200), random.randint(120, 180))
            self.effects.append(Particle(pos, (vx, vy), radius=radius, duration_ms=life_ms, color=color))

    def _update_effects(self, now: int):
        dt = max(0, now - self.last_effect_tick)
        self.last_effect_tick = now
        for effect in self.effects[:]:
            if isinstance(effect, Particle):
                effect.update(dt)
                if effect.is_dead(now):
                    self.effects.remove(effect)
            elif isinstance(effect, AnimatedEffect):
                if effect.is_dead(now):
                    self.effects.remove(effect)
            elif isinstance(effect, TimedSpriteEffect):
                if effect.is_dead(now):
                    self.effects.remove(effect)
            elif isinstance(effect, TrailDot):
                if effect.is_dead(now):
                    self.effects.remove(effect)

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
                self._update_effects(now)

                # Rapid fire expiration
                if now > self.rapid_fire_until and self.current_cooldown != self.BASE_BULLET_COOLDOWN_MS:
                    self.current_cooldown = self.BASE_BULLET_COOLDOWN_MS

                # Firing logic with cooldown
                if keys[pygame.K_f] or keys[pygame.K_SPACE]:
                    if now - self.last_shot_time >= self.current_cooldown:
                        bullet = Bullet(
                            self.plane.rect.centerx,
                            self.plane.rect.top,
                            image_surface=self.bullet_surface,
                        )
                        self.bullets.append(bullet)
                        self.last_shot_time = now
                        self._spawn_muzzle_flash()

                # Move airplane
                self.plane.move(keys, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

                # Move bullets
                for bullet in self.bullets[:]:
                    bullet.move()
                    if now - bullet.last_trail_tick >= 40:
                        self._spawn_trail_dot(bullet.rect.center)
                        bullet.last_trail_tick = now
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
                            enemy.start_flash()
                            if enemy.hit(bullet.damage):
                                if enemy in self.enemies:
                                    self._spawn_explosion(enemy.rect.center)
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
                        self.plane.start_flash()
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
            else:
                # Let lingering effects expire even when paused or game over
                self._update_effects(pygame.time.get_ticks())

            # Draw everything
            draw_now = pygame.time.get_ticks()
            if self.background_mode == "static" and self.static_background is not None:
                self.screen.blit(self.static_background, (0, 0))
            else:
                self.screen.fill(self.BACKGROUND_COLOR)
                if self.starfield:
                    self.starfield.update_and_draw(self.screen)
            self.plane.draw(self.screen, draw_now)

            for bullet in self.bullets:
                bullet.draw(self.screen)

            for enemy in self.enemies:
                enemy.draw(self.screen, draw_now)

            for item in self.powerups:
                item.draw(self.screen)

            for effect in self.effects:
                if isinstance(effect, AnimatedEffect):
                    effect.draw(self.screen, draw_now)
                elif isinstance(effect, TrailDot):
                    effect.draw(self.screen, draw_now)
                elif isinstance(effect, Particle):
                    effect.draw(self.screen, draw_now)
                else:
                    effect.draw(self.screen)

            self.draw_hud()

            if self.paused and not self.game_over:
                self.draw_pause()

            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(self.FPS)
