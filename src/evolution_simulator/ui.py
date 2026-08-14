"""Наглядный интерфейс симулятора. Вся эволюционная логика живёт не здесь."""

from __future__ import annotations

import colorsys
from dataclasses import dataclass


SKY = (177, 220, 245)
SOIL = (105, 72, 43)
DEEP_SOIL = (72, 49, 34)
LAKE = (45, 145, 210)
LAKE_LIGHT = (100, 205, 240)
PANEL = (26, 34, 42)
TEXT = (238, 244, 246)
MUTED = (165, 183, 192)
ACCENT = (102, 210, 132)


def plant_color(plant) -> tuple[int, int, int]:
    red, green, blue = colorsys.hsv_to_rgb(plant.genome.color_hue, 0.72, 0.78)
    return int(red * 255), int(green * 255), int(blue * 255)


@dataclass(frozen=True)
class Layout:
    cell: int
    world_left: int
    world_top: int
    world_width: int
    world_height: int
    panel_left: int


def calculate_layout(screen_size: tuple[int, int], world_size: tuple[int, int]) -> Layout:
    screen_width, screen_height = screen_size
    panel_width = max(300, min(370, screen_width // 4))
    available_width = screen_width - panel_width - 24
    available_height = screen_height - 24
    cell = max(4, min(14, available_width // world_size[0], available_height // world_size[1]))
    world_width, world_height = world_size[0] * cell, world_size[1] * cell
    world_left = max(8, (available_width - world_width) // 2)
    world_top = max(8, (screen_height - world_height) // 2)
    return Layout(cell, world_left, world_top, world_width, world_height, screen_width - panel_width)


def _cell_rect(pygame, layout: Layout, x: int, y: int):
    return pygame.Rect(layout.world_left + x * layout.cell, layout.world_top + y * layout.cell,
                       layout.cell + 1, layout.cell + 1)


def _draw_world(pygame, screen, simulation, layout: Layout, show_water: bool) -> None:
    world = simulation.world
    world_rect = pygame.Rect(layout.world_left, layout.world_top, layout.world_width, layout.world_height)
    pygame.draw.rect(screen, SKY, world_rect)

    # Солнце и облака дают понятный визуальный контекст, но не влияют на формулы.
    pygame.draw.circle(screen, (255, 225, 105), (layout.world_left + layout.world_width - 55, layout.world_top + 50), 24)
    for offset in (0, 32, 60):
        pygame.draw.circle(screen, (238, 246, 250), (layout.world_left + 90 + offset, layout.world_top + 48), 22)

    ground_y = world.ground_y
    soil_top = layout.world_top + (ground_y + 1) * layout.cell
    pygame.draw.rect(screen, SOIL, (layout.world_left, soil_top, layout.world_width, world.soil_depth * layout.cell))
    pygame.draw.rect(screen, DEEP_SOIL, (layout.world_left, soil_top + world.soil_depth * layout.cell // 2,
                                         layout.world_width, world.soil_depth * layout.cell // 2))

    # Озеро занимает левую сторону и немного заходит выше линии земли.
    lake_surface_y = layout.world_top + (ground_y - 4) * layout.cell
    lake_width_px = world.lake_width * layout.cell
    pygame.draw.rect(screen, LAKE, (layout.world_left, lake_surface_y, lake_width_px,
                                    layout.world_height - (ground_y - 4) * layout.cell))
    for wave in range(3):
        y = lake_surface_y + 5 + wave * max(4, layout.cell)
        pygame.draw.line(screen, LAKE_LIGHT, (layout.world_left + 8, y),
                         (layout.world_left + lake_width_px - 8, y), max(1, layout.cell // 5))

    # Берег обозначает переход от постоянного источника воды к почве.
    shore_x = layout.world_left + lake_width_px
    pygame.draw.polygon(screen, (166, 132, 76), [(shore_x - 2 * layout.cell, soil_top),
                                                  (shore_x + 3 * layout.cell, soil_top),
                                                  (shore_x - 1 * layout.cell, lake_surface_y)])

    if show_water:
        for x, value in enumerate(world.water):
            if x < world.lake_width:
                continue
            blue = int(45 + 150 * value)
            overlay = pygame.Surface((layout.cell, world.soil_depth * layout.cell), pygame.SRCALPHA)
            overlay.fill((30, 100, blue, int(35 + 95 * value)))
            screen.blit(overlay, (layout.world_left + x * layout.cell, soil_top))

    pygame.draw.rect(screen, (52, 66, 72), world_rect, 2)


def _draw_plants(pygame, screen, simulation, layout: Layout, selected) -> None:
    for plant in simulation.plants:
        stem = plant_color(plant)
        root_screen = (layout.world_left + plant.root_x * layout.cell + layout.cell // 2,
                       layout.world_top + simulation.world.ground_y * layout.cell + layout.cell // 2)
        top_y = min(y for _, y in plant.cells)
        top_screen = (root_screen[0], layout.world_top + top_y * layout.cell + layout.cell // 2)
        # Сплошной стебель читается лучше, чем отдельные квадратные клетки.
        pygame.draw.line(screen, stem, root_screen, top_screen, max(2, layout.cell // 2))
        for x, y in sorted(plant.cells):
            center = (layout.world_left + x * layout.cell + layout.cell // 2,
                      layout.world_top + y * layout.cell + layout.cell // 2)
            if (x, y) in plant.leaves:
                branch_point = (root_screen[0], center[1])
                pygame.draw.line(screen, stem, branch_point, center, max(2, layout.cell // 3))
                radius = max(3, layout.cell // 2 + plant.genome.leaf_size)
                pygame.draw.circle(screen, (66, 168, 76), center, radius)
                pygame.draw.circle(screen, (135, 220, 104), center, max(1, radius // 2))
        if plant is selected:
            rect = pygame.Rect(layout.world_left + (plant.root_x - 3) * layout.cell,
                               layout.world_top + (top_y - 2) * layout.cell,
                               7 * layout.cell, (plant.height + 4) * layout.cell)
            pygame.draw.rect(screen, (255, 236, 120), rect, 2)


def _draw_graph(pygame, screen, font, simulation, rect) -> None:
    pygame.draw.rect(screen, (18, 24, 30), rect, border_radius=6)
    values = [item.population for item in simulation.history[-180:]]
    if len(values) < 2:
        return
    maximum = max(1, max(values))
    points = []
    for index, value in enumerate(values):
        x = rect.left + 8 + index * (rect.width - 16) / (len(values) - 1)
        y = rect.bottom - 8 - value / maximum * (rect.height - 25)
        points.append((round(x), round(y)))
    pygame.draw.lines(screen, ACCENT, False, points, 2)
    screen.blit(font.render(f"Популяция за последние шаги (макс. {maximum})", True, MUTED), (rect.left + 8, rect.top + 5))


def _button(pygame, screen, font, rect, label: str, active: bool = False) -> None:
    color = (62, 125, 82) if active else (50, 64, 73)
    pygame.draw.rect(screen, color, rect, border_radius=6)
    text = font.render(label, True, TEXT)
    screen.blit(text, text.get_rect(center=rect.center))


def _draw_panel(pygame, screen, simulation, layout: Layout, font, small_font, paused: bool,
                speed: int, selected, show_water: bool):
    panel_rect = pygame.Rect(layout.panel_left, 0, screen.get_width() - layout.panel_left, screen.get_height())
    pygame.draw.rect(screen, PANEL, panel_rect)
    x = layout.panel_left + 18
    snapshot = simulation.snapshot()
    lines = [
        ("ЭВОЛЮЦИЯ РАСТЕНИЙ", TEXT),
        (f"Шаг: {simulation.tick}", MUTED),
        (f"Растений: {snapshot.population}", TEXT),
        (f"Поколение: {snapshot.generations}", TEXT),
        (f"Сезон: {getattr(simulation, 'season', 'весна')}", TEXT),
        (f"Средняя высота: {snapshot.avg_height:.1f}", TEXT),
    ]
    y = 18
    for line, color in lines:
        screen.blit(font.render(line, True, color), (x, y)); y += 27

    graph_rect = pygame.Rect(x, y + 5, panel_rect.width - 36, 115)
    _draw_graph(pygame, screen, small_font, simulation, graph_rect)
    y = graph_rect.bottom + 15

    pause_rect = pygame.Rect(x, y, 118, 36)
    reset_rect = pygame.Rect(x + 128, y, 118, 36)
    _button(pygame, screen, small_font, pause_rect, "Продолжить" if paused else "Пауза", paused)
    _button(pygame, screen, small_font, reset_rect, "Новый мир")
    y += 48
    speed_rects = []
    for index, value in enumerate((1, 3, 8)):
        rect = pygame.Rect(x + index * 82, y, 72, 34); speed_rects.append((rect, value))
        _button(pygame, screen, small_font, rect, f"×{value}", speed == value)
    y += 45
    water_rect = pygame.Rect(x, y, 246, 34)
    _button(pygame, screen, small_font, water_rect, "Скрыть воду" if show_water else "Показать воду", show_water)
    y += 48

    if selected and selected.alive:
        labels = [
            f"Растение #{selected.id}, поколение {selected.generation}",
            f"Энергия: {selected.energy:.1f}   Возраст: {selected.age}",
            f"Скорость роста: {selected.genome.growth_rate:.2f}",
            f"Макс. высота: {selected.genome.max_height}",
            f"Ветвление: {selected.genome.branching:.2f}",
            f"Размер листа: {selected.genome.leaf_size}",
            f"Фотосинтез: {selected.genome.photosynthesis:.2f}",
            f"Метаболизм: {selected.genome.metabolism:.2f}",
        ]
    else:
        labels = ["Нажмите на растение,", "чтобы увидеть его геном.", "", "Озеро слева постоянно", "увлажняет ближайшую почву."]
    for line in labels:
        screen.blit(small_font.render(line, True, TEXT if line else MUTED), (x, y)); y += 22
    return pause_rect, reset_rect, speed_rects, water_rect


def run(simulation) -> None:
    import pygame

    pygame.init()
    info = pygame.display.Info()
    width = min(1500, max(1000, int(info.current_w * 0.9)))
    height = min(900, max(650, int(info.current_h * 0.85)))
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    pygame.display.set_caption("Эволюция растений — озеро, ресурсы и генетика")
    font = pygame.font.SysFont("Arial", 20)
    small_font = pygame.font.SysFont("Arial", 16)
    clock = pygame.time.Clock()
    paused, speed, selected, show_water, running = False, 3, None, True, True
    controls = None

    while running:
        layout = calculate_layout(screen.get_size(), (simulation.config.width, simulation.config.height))
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                paused = not paused
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                simulation.reset(); selected = None
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_w:
                show_water = not show_water
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                speed = {pygame.K_1: 1, pygame.K_2: 3, pygame.K_3: 8}[event.key]
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if controls:
                    pause_rect, reset_rect, speed_rects, water_rect = controls
                    if pause_rect.collidepoint(event.pos): paused = not paused
                    elif reset_rect.collidepoint(event.pos): simulation.reset(); selected = None
                    elif water_rect.collidepoint(event.pos): show_water = not show_water
                    else:
                        for rect, value in speed_rects:
                            if rect.collidepoint(event.pos): speed = value
                if event.pos[0] < layout.panel_left:
                    world_x = (event.pos[0] - layout.world_left) // layout.cell
                    world_y = (event.pos[1] - layout.world_top) // layout.cell
                    selected = simulation.selected_at(world_x, world_y)

        if not paused:
            for _ in range(speed):
                simulation.step()
        if selected and not selected.alive:
            selected = None

        screen.fill((12, 18, 24))
        _draw_world(pygame, screen, simulation, layout, show_water)
        _draw_plants(pygame, screen, simulation, layout, selected)
        controls = _draw_panel(pygame, screen, simulation, layout, font, small_font,
                               paused, speed, selected, show_water)
        pygame.display.flip()
        clock.tick(30)
    pygame.quit()
