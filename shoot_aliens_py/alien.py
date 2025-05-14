import pygame

class Alien:
    def __init__(self, x, y, speed=5):
        # Load and resize alien image
        self.image = pygame.image.load("res/alien.png")
        self.image = pygame.transform.scale(self.image, (80, 80))  # Resize to 80x80 pixels
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = speed

    def move(self):
        """Move the alien downwards."""
        self.rect.y += self.speed

    def is_off_screen(self, height):
        """Check if the alien is off the screen."""
        return self.rect.top > height

    def draw(self, screen):
        """Draw the alien on the screen."""
        screen.blit(self.image, self.rect)

    def check_collision(self, bullet):
        """Check for collision with a bullet."""
        return self.rect.colliderect(bullet.rect)

def main():
    # Initialize pygame
    pygame.init()

    # Screen dimensions
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600

    # Create screen
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Alien Test")

    # Clock for controlling frame rate
    clock = pygame.time.Clock()

    # Create an alien instance
    alien = Alien(WINDOW_WIDTH // 2, 0)

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Move the alien
        alien.move()

        # Check if the alien is off-screen
        if alien.is_off_screen(WINDOW_HEIGHT):
            print("Alien went off-screen!")
            running = False

        # Draw everything
        screen.fill((0, 0, 0))  # Clear screen with black
        alien.draw(screen)
        pygame.display.flip()

        # Cap the frame rate
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()