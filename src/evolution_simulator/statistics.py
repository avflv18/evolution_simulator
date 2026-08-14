from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class Snapshot:
    tick: int
    population: int
    generations: int
    avg_height: float
    avg_growth_rate: float
    min_growth_rate: float
    max_growth_rate: float
    avg_photosynthesis: float


def snapshot(tick: int, plants) -> Snapshot:
    living = [plant for plant in plants if plant.alive]
    if not living: return Snapshot(tick, 0, 0, 0, 0, 0, 0, 0)
    growth = [p.genome.growth_rate for p in living]
    return Snapshot(tick, len(living), max(p.generation for p in living), mean(p.height for p in living),
                    mean(growth), min(growth), max(growth), mean(p.genome.photosynthesis for p in living))
