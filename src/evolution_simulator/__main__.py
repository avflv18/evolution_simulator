import argparse
from pathlib import Path

from .config import SimulationConfig
from .simulation import Simulation
from .ui import run


def main():
    parser = argparse.ArgumentParser(description="Симулятор эволюции растений")
    parser.add_argument("--seed", type=int); parser.add_argument("--config", type=Path)
    parser.add_argument("--headless", type=int, metavar="STEPS"); args = parser.parse_args()
    config = SimulationConfig.from_json(args.config) if args.config else SimulationConfig()
    if args.seed is not None: config = SimulationConfig(**{**config.__dict__, "seed": args.seed})
    simulation = Simulation(config)
    if args.headless:
        for _ in range(args.headless): simulation.step()
        print(simulation.snapshot())
    else: run(simulation)


if __name__ == "__main__": main()
