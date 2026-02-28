import pygame
import sys


class Airplane:
    """Player-controlled ship that moves within the screen and renders its sprite."""

    def __init__(self, image_path, plane_width, plane_height, init_pos_x, init_pos_y, speed = 10):
        """Load the plane sprite, size it, position it, and store movement speed."""
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (plane_width, plane_height))
        self.rect = self.image.get_rect()
        self.rect.center = (init_pos_x, init_pos_y)
        self.speed = speed
        self.flash_until = 0

    def move(self, keys, window_width, window_height):
        """Update position based on pressed keys while clamping to window bounds."""
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < window_width:
            self.rect.x += self.speed
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN] and self.rect.bottom < window_height:
            self.rect.y += self.speed

    def getPos(self):
        """Return current (x, y) position of the plane's rect."""
        return self.rect.x, self.rect.y

    def start_flash(self, duration_ms: int = 120):
        """Trigger a temporary bright flash overlay (damage feedback)."""
        self.flash_until = pygame.time.get_ticks() + duration_ms

    def draw(self, screen, now: int | None = None):
        """Blit the plane sprite; tint white briefly if flashing."""
        now = now or pygame.time.get_ticks()
        if now < self.flash_until:
            flash_img = self.image.copy()
            flash_img.fill((255, 255, 255, 160), None, pygame.BLEND_RGBA_ADD)
            screen.blit(flash_img, self.rect)
        else:
            screen.blit(self.image, self.rect)