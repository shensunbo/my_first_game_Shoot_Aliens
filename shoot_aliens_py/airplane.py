import pygame
import sys

class Airplane:
    def __init__(self, image_path, plane_width, plane_height, init_pos_x, init_pos_y, speed = 10):
        # Load and resize airplane image
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (plane_width, plane_height))
        self.rect = self.image.get_rect()
        self.rect.center = (init_pos_x, init_pos_y)
        self.speed = speed

    def move(self, keys, window_width):
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < window_width:
            self.rect.x += self.speed

    def draw(self, screen):
        screen.blit(self.image, self.rect)