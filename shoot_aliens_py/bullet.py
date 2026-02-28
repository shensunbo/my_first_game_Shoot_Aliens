import pygame

class Bullet:
    def __init__(self, x, y, damage: int = 1):
        # Load and resize bullet image
        self.image = pygame.image.load("res/bullet.png")
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 15
        self.damage = damage

    def move(self):
        """Move the bullet upwards."""
        self.rect.y -= self.speed

    def is_off_screen(self, height):
        """Check if the bullet is off the screen."""
        return self.rect.bottom < 0

    def draw(self, screen):
        """Draw the bullet on the screen."""
        screen.blit(self.image, self.rect)