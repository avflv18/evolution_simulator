import math


class World:
    def __init__(self, width: int, height: int, soil_depth: int, initial_water: float, regeneration: float,
                 light_level: float, lake_width: int = 0):
        self.width, self.height, self.soil_depth = width, height, soil_depth
        self.lake_width = lake_width
        self.regeneration, self.light_level = regeneration, light_level
        # Озеро постоянно подпитывает ближайшую почву. Чем дальше берег,
        # тем слабее его влияние.
        self.water = [self._starting_water(x, initial_water) for x in range(width)]
        self.occupied: dict[tuple[int, int], int] = {}

    def _starting_water(self, x: int, base: float) -> float:
        if x < self.lake_width:
            return 1.0
        distance = x - self.lake_width
        return min(1.0, base + 0.42 * math.exp(-distance / 16))

    @property
    def ground_y(self) -> int:
        return self.height - self.soil_depth - 1

    def inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y <= self.ground_y

    def is_free(self, x: int, y: int) -> bool:
        # Корень не может появиться на поверхности озера.
        if y == self.ground_y and x < self.lake_width:
            return False
        # Между корнями оставляем хотя бы одну клетку: отдельные растения
        # легче различать, и популяция не превращается в сплошную стену.
        if y == self.ground_y:
            if any((x + offset, y) in self.occupied for offset in (-1, 0, 1)):
                return False
        return self.inside(x, y) and (x, y) not in self.occupied

    def distance_to_lake(self, x: int) -> int:
        return max(0, x - self.lake_width)

    def occupy(self, plant_id: int, cells: set[tuple[int, int]]) -> None:
        for cell in cells:
            # Внутри уже созданного растения соседние клетки допустимы.
            blocked = not self.inside(*cell) or cell in self.occupied
            if blocked and self.occupied.get(cell) != plant_id:
                raise ValueError(f"Клетка занята: {cell}")
        for cell in cells: self.occupied[cell] = plant_id

    def release(self, plant_id: int) -> None:
        self.occupied = {cell: owner for cell, owner in self.occupied.items() if owner != plant_id}

    def light_at(self, x: int, y: int, season_factor: float = 1.0) -> float:
        blockers = sum(1 for (cell_x, cell_y) in self.occupied if cell_x == x and cell_y < y)
        return self.light_level * season_factor * math.exp(-0.32 * blockers)

    def consume_water(self, x: int, amount: float) -> float:
        x = min(self.width - 1, max(0, x))
        taken = min(self.water[x], max(0.0, amount))
        self.water[x] -= taken
        return taken

    def regenerate(self, season_factor: float = 1.0) -> None:
        for index, value in enumerate(self.water):
            if index < self.lake_width:
                self.water[index] = 1.0
                continue
            lake_bonus = 0.018 * math.exp(-self.distance_to_lake(index) / 14)
            self.water[index] = min(1.0, value + (self.regeneration + lake_bonus) * season_factor)
