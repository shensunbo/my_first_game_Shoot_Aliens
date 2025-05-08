# code for airplane shoot aliens game

import pygame
import sys
from airplane import Airplane 

# Initialize pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
FPS = 30
AIRPLANE_SPEED = 10

# Initialize screen
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Airplane Game")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Main game loop
def main():

    plane = Airplane("res/airplane.png", 100, 100, WINDOW_WIDTH // 2, WINDOW_HEIGHT - 150, AIRPLANE_SPEED)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Get keys pressed
        keys = pygame.key.get_pressed()
        # Move airplane
        plane.move(keys, WINDOW_WIDTH)

        # Draw everything
        screen.fill((0, 0, 0))  # Clear screen with black
        plane.draw(screen)
        
        pygame.display.flip()  # Update display

        # Cap the frame rate
        clock.tick(FPS)

if __name__ == "__main__":
    main()