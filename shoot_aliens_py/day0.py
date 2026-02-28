"""Entry point: selection screen then launches the Game loop contained in `game.py`."""

import sys
from pathlib import Path

import pygame

from config import load_config
from game import Game


def selection_screen():
    cfg = load_config()
    width, height = cfg["window"]["width"], cfg["window"]["height"]

    player_options = [
        ("Pilot A", "res/player/airplane.png"),
        ("Pilot B", "res/player/finger.png"),
    ]
    bullet_options = [
        ("Bullet", "res/bullet/bullet.png"),
        ("Tomato", "res/bullet/tomato.png"),
    ]

    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Select Loadout")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 42)
    small = pygame.font.Font(None, 28)

    def load_preview(path: str, size: tuple[int, int]):
        surf = pygame.image.load(Path(path)).convert_alpha()
        return pygame.transform.scale(surf, size)

    previews = {
        "player": {p: load_preview(path, (180, 180)) for _, path in player_options for p in [path]},
        "bullet": {p: load_preview(path, (90, 90)) for _, path in bullet_options for p in [path]},
    }

    p_idx, b_idx = 0, 0
    phase = "player"  # player -> bullet

    def draw_option(center: tuple[int, int], img: pygame.Surface, label: str, focused: bool, confirmed: bool = False):
        rect = img.get_rect(center=center)
        screen.blit(img, rect)
        text_color = (230, 230, 230) if not confirmed else (180, 255, 200)
        text = small.render(label, True, text_color)
        text_rect = text.get_rect(midtop=(rect.centerx, rect.bottom + 8))
        screen.blit(text, text_rect)
        if focused:
            border_color = (255, 215, 0)  # gold for current focus
        elif confirmed:
            border_color = (120, 200, 140)  # greenish for locked-in choice
        else:
            border_color = (80, 90, 110)
        pygame.draw.rect(screen, border_color, rect.inflate(12, 12), width=3, border_radius=10)

    player_locked = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit()
                    sys.exit()
                if phase == "player":
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        p_idx = (p_idx + 1) % len(player_options)
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        phase = "bullet"
                        player_locked = True
                else:  # bullet phase
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                        b_idx = (b_idx + 1) % len(bullet_options)
                    if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                        selected = {
                            "player": player_options[p_idx][1],
                            "bullet": bullet_options[b_idx][1],
                        }
                        pygame.quit()
                        return selected

        screen.fill((8, 10, 26))

        title_txt = "Step 1/2: Choose Player (Enter to confirm)" if phase == "player" else "Step 2/2: Choose Bullet (Enter to start)"
        title = font.render(title_txt, True, (240, 240, 240))
        screen.blit(title, title.get_rect(center=(width // 2, 80)))

        # Player options side by side
        pl_positions = [width // 3 - 140, width // 3 + 140]
        for i, (label, path) in enumerate(player_options):
            img = previews["player"][path]
            draw_option(
                (pl_positions[i], height // 2),
                img,
                label,
                focused=(i == p_idx and phase == "player"),
                confirmed=player_locked and i == p_idx,
            )

        # Bullet options side by side
        bl_positions = [2 * width // 3 - 100, 2 * width // 3 + 100]
        for i, (label, path) in enumerate(bullet_options):
            img = previews["bullet"][path]
            draw_option(
                (bl_positions[i], height // 2 + 40),
                img,
                label,
                focused=(phase == "bullet" and i == b_idx),
                confirmed=False,
            )

        hint = small.render("Esc/Q: Quit  Enter: Confirm", True, (180, 180, 180))
        screen.blit(hint, hint.get_rect(center=(width // 2, height - 60)))

        pygame.display.flip()
        clock.tick(60)


def main():
    assets = selection_screen()
    Game(selected_assets=assets).run()


if __name__ == "__main__":
    main()