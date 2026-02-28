import pygame
import random


class Enemy:
    """Enemy ship that moves downward with optional drift and tracks HP/score value."""

    def __init__(self, image_path, width, height, x, y, speed, drift=0, hp=1, score_value=10):
        """Initialize enemy sprite, position, movement, health, and score reward."""
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.drift = drift
        self.hp = hp
        self.score_value = score_value

    def move(self, window_width):
        """Advance enemy downward and apply horizontal drift within screen bounds."""
        self.rect.y += self.speed
        self.rect.x += self.drift
        if self.rect.left < 0:
            self.rect.left = 0
            self.drift = abs(self.drift)
        elif self.rect.right > window_width:
            self.rect.right = window_width
            self.drift = -abs(self.drift)

    def hit(self, damage: int = 1):
        """Apply damage and return True if enemy is destroyed."""
        self.hp -= damage
        return self.hp <= 0

    def is_off_screen(self, window_width, window_height):
        """Return True if enemy has left the play area."""
        return self.rect.top > window_height or self.rect.right < 0 or self.rect.left > window_width

    def draw(self, screen):
        """Render the enemy sprite."""
        screen.blit(self.image, self.rect)
