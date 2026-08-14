from dataclasses import dataclass, field
import random

from .genetics import Genome


@dataclass
class Plant:
    id: int
    root_x: int
    genome: Genome
    generation: int = 0
    energy: float = 8.0
    age: int = 0
    offspring: int = 0
    alive: bool = True
    cells: set[tuple[int, int]] = field(default_factory=set)
    leaves: set[tuple[int, int]] = field(default_factory=set)
    growth_credit: float = 0.0
    total_energy: float = 0.0

    def initialize(self, ground_y: int) -> None:
        self.cells.add((self.root_x, ground_y))

    @property
    def height(self) -> int:
        if not self.cells: return 0
        return max(y for _, y in self.cells) - min(y for _, y in self.cells) + 1

    def fitness(self) -> float:
        return self.age + self.offspring * 50 + self.total_energy * 0.05

    def update(self, world, rng: random.Random, light_factor: float, mutation_rate: float) -> list[tuple[int, Genome, int]]:
        if not self.alive: return []
        self.age += 1
        requested_water = 0.025 + len(self.cells) * 0.001
        water = world.consume_water(self.root_x, requested_water)
        water_factor = water / requested_water if requested_water else 0.0
        gained = 0.0
        for x, y in self.leaves or {(self.root_x, min(y for _, y in self.cells))}:
            gained += world.light_at(x, y, light_factor) * self.genome.photosynthesis * water_factor * 0.55
        self.energy += gained - self.genome.metabolism * (1 + len(self.cells) * 0.08)
        self.total_energy += max(0.0, gained)
        self.growth_credit += self.genome.growth_rate
        if self.growth_credit >= 1 and self.energy > 2:
            self.growth_credit -= 1
            self._grow(world, rng)
        children = []
        if self.age >= self.genome.reproduction_age and self.energy >= 20:
            # Семя падает не вплотную к родителю: растения остаются различимыми.
            direction = rng.choice((-6, -5, -4, -3, 3, 4, 5, 6))
            child_x = self.root_x + direction
            if world.is_free(child_x, world.ground_y):
                self.energy -= 10; self.offspring += 1
                children.append((child_x, self.genome.mutated(rng, mutation_rate), self.generation + 1))
        if self.energy <= 0 or self.age > 500:
            self.alive = False
        return children

    def _grow(self, world, rng: random.Random) -> None:
        top_y = min(y for _, y in self.cells)
        if self.height < self.genome.max_height:
            target = (self.root_x, top_y - 1)
            if world.is_free(*target):
                # Верхний лист поднимается вместе с растущим стеблем.
                self.leaves.discard((self.root_x, top_y))
                self.cells.add(target); world.occupy(self.id, {target}); self.energy -= 0.8
                if self.height >= 3: self.leaves.add(target)
        if self.height >= 3 and rng.random() < self.genome.branching:
            direction = rng.choice((-1, 1)); target = (self.root_x + direction * self.genome.leaf_size, top_y)
            if world.is_free(*target):
                self.cells.add(target); self.leaves.add(target); world.occupy(self.id, {target}); self.energy -= 0.5
