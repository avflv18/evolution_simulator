import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

from evolution_simulator.genetics import Genome
from evolution_simulator.organisms import Plant
from evolution_simulator.ui import plant_color


def test_pygame_display_and_color_smoke():
    import pygame
    pygame.init()
    try:
        screen = pygame.display.set_mode((32, 32))
        color = plant_color(Plant(1, 1, Genome()))
        screen.fill(color); pygame.display.flip()
        assert all(0 <= component <= 255 for component in color)
    finally:
        pygame.quit()
