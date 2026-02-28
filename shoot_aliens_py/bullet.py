import pygame


class Bullet:
    """Player projectile that travels upward and damages enemies."""

    def __init__(self, x, y, damage: int = 1):
        """Create a bullet sprite at (x, y) with given damage value."""
        self.image = pygame.image.load("res/bullet.png")
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 15
        self.damage = damage

    def move(self):
        """Advance the bullet upward each frame."""
        self.rect.y -= self.speed

    def is_off_screen(self, height):
        """Return True if bullet has left the visible window."""
        return self.rect.bottom < 0

    def draw(self, screen):
        """Render the bullet sprite."""
        screen.blit(self.image, self.rect)