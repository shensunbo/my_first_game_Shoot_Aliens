import pygame
import random

class Enemy:
    def __init__(self, image_path, width, height, x, y, speed, drift=0):
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (width, height))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed
        self.drift = drift

    def move(self, window_width):
        self.rect.y += self.speed
        self.rect.x += self.drift
        # Keep slight horizontal drift within screen bounds
        if self.rect.left < 0:
            self.rect.left = 0
            self.drift = abs(self.drift)
        elif self.rect.right > window_width:
            self.rect.right = window_width
            self.drift = -abs(self.drift)

    def is_off_screen(self, window_width, window_height):
        return self.rect.top > window_height or self.rect.right < 0 or self.rect.left > window_width

    def draw(self, screen):
        screen.blit(self.image, self.rect)
