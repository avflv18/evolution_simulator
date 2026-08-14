import argparse
import csv
from dataclasses import asdict, replace
from pathlib import Path

from .config import SimulationConfig
from .simulation import Simulation

SCENARIOS = {"stable": {}, "low_light": {"light_level": 0.55}, "low_water": {"initial_water": 0.3, "water_regeneration": 0.004}}


def run_experiments(scenario: str, runs: int, steps: int, output: str | Path, base: SimulationConfig | None = None) -> Path:
    destination = Path(output); destination.parent.mkdir(parents=True, exist_ok=True)
    config = replace(base or SimulationConfig(), **SCENARIOS[scenario])
    with destination.open("w", encoding="utf-8", newline="") as stream:
        fieldnames = ["run", "seed", *asdict(Simulation(config)).keys()] if False else ["run", "seed", "tick", "population", "generations", "avg_height", "avg_growth_rate", "min_growth_rate", "max_growth_rate", "avg_photosynthesis"]
        writer = csv.DictWriter(stream, fieldnames=fieldnames); writer.writeheader()
        for run in range(runs):
            simulation = Simulation(replace(config, seed=config.seed + run))
            for _ in range(steps): simulation.step()
            writer.writerow({"run": run, "seed": simulation.seed, **asdict(simulation.snapshot())})
    return destination


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--scenario", choices=SCENARIOS, default="stable")
    parser.add_argument("--runs", type=int, default=20); parser.add_argument("--steps", type=int, default=1000)
    parser.add_argument("--output", default="output/experiments.csv"); args = parser.parse_args()
    print(run_experiments(args.scenario, args.runs, args.steps, args.output))


if __name__ == "__main__": main()
