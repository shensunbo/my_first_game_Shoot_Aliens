# code for airplane shoot aliens gamz

import pygame
import sys
from airplane import Airplane 
from bullet import Bullet
from alien import Alien  # Import the Alien class
import random  # For random alien spawning

# Initialize pygame
pygame.init()

# ConstantsPz
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 720
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
    bullets = []
    aliens = []  # List to store aliens
    alien_spawn_timer = 0  # Timer to control alien spawning

    while True:
        screen.fill((0, 50, 50))  # Clear screen with black
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Get keys pressed
        keys = pygame.key.get_pressed()
        
        # Check for quit event
        if keys[pygame.K_ESCAPE]:
            break

        if keys[pygame.K_f]:
            bullet = Bullet(plane.getPos()[0] + 50, plane.getPos()[1])
            bullets.append(bullet)

        # Spawn aliens periodically
        alien_spawn_timer += 1
        if alien_spawn_timer > 60:  # Spawn an alien every 60 frames
            alien_x = random.randint(10, WINDOW_WIDTH - 80)  # Random x position
            aliens.append(Alien(alien_x, 0))  # Spawn alien at the top of the screen
            alien_spawn_timer = 0

        # Move airplane
        plane.move(keys, WINDOW_WIDTH)

        # Draw everything
        plane.draw(screen)
        
        # Move and draw aliens
        for alien in aliens[:]:
            alien.move()
            if alien.is_off_screen(WINDOW_HEIGHT):
                aliens.remove(alien)  # Remove alien if it goes off-screen
            alien.draw(screen)

        for bullet in bullets[:]:
            bullet.move()
            if bullet.is_off_screen(WINDOW_HEIGHT):
                bullets.remove(bullet)
            bullet.draw(screen)
            
        # # Check for collisions between bullets and aliens
        # for bullet in bullets[:]:
        #     for alien in aliens[:]:
        #         if alien.check_collision(bullet):
        #             bullets.remove(bullet)  # Remove bullet on collision
        #             aliens.remove(alien)  # Remove alien on collision
        #             break

        pygame.display.flip()  # Update display

        # Cap the frame rate
        clock.tick(FPS)

if __name__ == "__main__":
    main()