import random

from .config import SimulationConfig
from .genetics import Genome
from .organisms import Plant
from .resources import season_factors
from .statistics import snapshot
from .world import World


class Simulation:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.reset(config.seed)

    def reset(self, seed: int | None = None) -> None:
        self.seed = self.config.seed if seed is None else seed
        self.rng = random.Random(self.seed); self.tick = 0; self.next_id = 0
        self.world = World(self.config.width, self.config.height, self.config.soil_depth, self.config.initial_water,
                           self.config.water_regeneration, self.config.light_level, self.config.lake_width)
        self.plants: list[Plant] = []
        land = range(self.config.lake_width + 2, self.config.width)
        positions = self.rng.sample(land, min(self.config.initial_plants, len(land)))
        for x in positions: self._add_plant(x, Genome.random(self.rng), 0)
        self.history = [self.snapshot()]

    def _add_plant(self, x: int, genome: Genome, generation: int) -> Plant | None:
        if not self.world.is_free(x, self.world.ground_y): return None
        plant = Plant(self.next_id, x, genome, generation); self.next_id += 1
        plant.initialize(self.world.ground_y); self.world.occupy(plant.id, plant.cells); self.plants.append(plant)
        return plant

    def step(self):
        self.tick += 1
        light, rain, self.season = season_factors(self.tick, self.config.season_length)
        self.world.regenerate(rain)
        children = []
        for plant in list(self.plants): children.extend(plant.update(self.world, self.rng, light, self.config.mutation_rate))
        for plant in self.plants:
            if not plant.alive: self.world.release(plant.id)
        self.plants = [plant for plant in self.plants if plant.alive]
        for x, genome, generation in children: self._add_plant(x, genome, generation)
        current = self.snapshot(); self.history.append(current); return current

    def snapshot(self): return snapshot(self.tick, self.plants)

    def selected_at(self, x: int, y: int):
        owner = self.world.occupied.get((x, y))
        return next((p for p in self.plants if p.id == owner), None)
