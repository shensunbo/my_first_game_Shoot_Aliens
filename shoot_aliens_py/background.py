import random
import pygame


class Starfield:
    """Procedural scrolling starfield for a space backdrop."""

    def __init__(self, width: int, height: int, layers: int = 3, stars_per_layer: int = 60):
        self.width = width
        self.height = height
        self.layers = []
        # Each layer scrolls at different speed for parallax depth
        for i in range(layers):
            speed = 0.5 + i * 0.5
            size = 2 + i  # brighter/larger on faster layers
            color = (180, 180, 220) if i == layers - 1 else (120, 120, 180)
            stars = [self._random_star(size) for _ in range(stars_per_layer)]
            self.layers.append({"speed": speed, "stars": stars, "size": size, "color": color})

    def _random_star(self, size: int):
        return [random.randint(0, self.width), random.randint(0, self.height), size]

    def update_and_draw(self, surface: pygame.Surface):
        for layer in self.layers:
            speed = layer["speed"]
            size = layer["size"]
            color = layer["color"]
            stars = layer["stars"]
            for star in stars:
                star[1] += speed
                if star[1] > self.height:
                    star[0] = random.randint(0, self.width)
                    star[1] = -size
                pygame.draw.circle(surface, color, (int(star[0]), int(star[1])), size)
