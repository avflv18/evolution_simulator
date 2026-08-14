from dataclasses import dataclass, fields, replace
import random


@dataclass(frozen=True)
class Genome:
    growth_rate: float = 0.45
    max_height: int = 12
    branching: float = 0.25
    leaf_size: int = 2
    photosynthesis: float = 2
    metabolism: float = 0.12
    reproduction_age: int = 35
    color_hue: float = 0.33

    LIMITS = {"growth_rate": (0.1, 1.0), "max_height": (3, 25), "branching": (0.0, 0.8),
              "leaf_size": (1, 4), "photosynthesis": (0.4, 2.0), "metabolism": (0.04, 0.35),
              "reproduction_age": (10, 120), "color_hue": (0.15, 0.48)}

    def mutated(self, rng: random.Random, rate: float = 0.12) -> "Genome":
        values = {}
        for field in fields(self):
            value = getattr(self, field.name)
            low, high = self.LIMITS[field.name]
            if rng.random() < rate:
                value += rng.gauss(0, (high - low) * 0.08)
            value = max(low, min(high, value))
            if isinstance(getattr(self, field.name), int): value = int(round(value))
            values[field.name] = value
        return replace(self, **values)

    @classmethod
    def random(cls, rng: random.Random) -> "Genome":
        base = cls()
        return base.mutated(rng, 1.0)
