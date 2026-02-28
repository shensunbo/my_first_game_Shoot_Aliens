import pygame
import random

POWERUP_TYPES = (
    "heal",         # +1 life up to max
    "rapid_fire",   # faster cooldown for a duration
)

class PowerUp:
    def __init__(self, kind: str, x: int, y: int, size: int = 40, fall_speed: int = 4):
        self.kind = kind
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        color = (80, 200, 120) if kind == "heal" else (200, 200, 80)
        pygame.draw.circle(self.image, color, (size // 2, size // 2), size // 2)
        inner_color = (40, 120, 80) if kind == "heal" else (120, 120, 40)
        pygame.draw.circle(self.image, inner_color, (size // 2, size // 2), size // 3)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.fall_speed = fall_speed

    def move(self):
        self.rect.y += self.fall_speed

    def is_off_screen(self, height):
        return self.rect.top > height

    def draw(self, screen):
        screen.blit(self.image, self.rect)


def random_powerup_kind():
    return random.choice(POWERUP_TYPES)
