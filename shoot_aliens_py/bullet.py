import pygame


class Bullet:
    """Player projectile that travels upward and damages enemies."""

    def __init__(self, x, y, damage: int = 1, image_surface=None, image_path: str | None = None, size=(50, 50)):
        """Create a bullet sprite at (x, y) with given damage value.

        image_surface: optional preloaded surface to reuse (preferred for performance).
        image_path: optional path to load if no surface is provided.
        size: tuple for scaling when loading from path/surface.
        """
        if image_surface is not None:
            self.image = pygame.transform.scale(image_surface, size)
        else:
            path = image_path or "res/bullet.png"
            self.image = pygame.image.load(path)
            self.image = pygame.transform.scale(self.image, size)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 15
        self.damage = damage
        self.last_trail_tick = 0

    def move(self):
        """Advance the bullet upward each frame."""
        self.rect.y -= self.speed

    def is_off_screen(self, height):
        """Return True if bullet has left the visible window."""
        return self.rect.bottom < 0

    def draw(self, screen):
        """Render the bullet sprite."""
        screen.blit(self.image, self.rect)