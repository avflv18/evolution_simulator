from dataclasses import dataclass, fields
import json
from pathlib import Path


@dataclass(frozen=True)
class SimulationConfig:
    width: int = 140
    height: int = 70
    soil_depth: int = 10
    lake_width: int = 10
    initial_plants: int = 22
    initial_water: float = 0.52
    water_regeneration: float = 0.008
    light_level: float = 1.0
    season_length: int = 400
    mutation_rate: float = 0.12
    seed: int = 42

    def __post_init__(self):
        if self.width < 20 or self.height < 20 or not 1 <= self.soil_depth < self.height:
            raise ValueError("Некорректный размер мира")
        if not 2 <= self.lake_width <= self.width - 3:
            raise ValueError("Озеро должно оставлять не менее трёх клеток суши")
        if self.initial_plants < 1 or self.season_length < 1:
            raise ValueError("Численность и длина сезона должны быть положительными")
        if not 0 <= self.initial_water <= 1 or not 0 <= self.light_level <= 1 or not 0 <= self.mutation_rate <= 1:
            raise ValueError("Ресурсы и вероятность должны быть в диапазоне 0..1")

    @classmethod
    def from_json(cls, path: str | Path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        allowed = {field.name for field in fields(cls)}
        if set(data) - allowed:
            raise ValueError("Конфигурация содержит неизвестные параметры")
        return cls(**data)
