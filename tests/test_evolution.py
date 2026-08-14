import random

from evolution_simulator.config import SimulationConfig
from evolution_simulator.experiments import run_experiments
from evolution_simulator.genetics import Genome
from evolution_simulator.organisms import Plant
from evolution_simulator.simulation import Simulation
from evolution_simulator.world import World


def test_genome_mutation_limits_and_zero_rate():
    genome = Genome(); rng = random.Random(1)
    assert genome.mutated(rng, 0) == genome
    for _ in range(100):
        genome = genome.mutated(rng, 1)
        for name, (low, high) in Genome.LIMITS.items(): assert low <= getattr(genome, name) <= high


def test_water_and_shadow():
    world = World(10, 10, 2, 0.5, 0.1, 1)
    assert world.consume_water(2, 0.2) == 0.2
    world.occupy(1, {(2, 2)})
    assert world.light_at(2, 4) < world.light_at(3, 4)


def test_lake_blocks_roots_and_waters_nearby_soil():
    world = World(40, 20, 4, 0.2, 0.001, 1, lake_width=6)
    assert not world.is_free(2, world.ground_y)
    assert world.is_free(8, world.ground_y)
    assert world.water[7] > world.water[35]
    before = world.water[7]
    world.consume_water(7, 0.1)
    world.regenerate()
    assert world.water[7] > before - 0.1


def test_occupied_cell_rejected():
    world = World(10, 10, 2, 1, 0, 1); world.occupy(1, {(2, 2)})
    try: world.occupy(2, {(2, 2)}); assert False
    except ValueError: pass


def test_roots_keep_visual_spacing():
    world = World(20, 20, 4, 1, 0, 1, lake_width=3)
    world.occupy(1, {(8, world.ground_y)})
    assert not world.is_free(9, world.ground_y)
    assert world.is_free(10, world.ground_y)


def test_plant_dies_without_energy():
    world = World(10, 10, 2, 0, 0, 0); plant = Plant(1, 2, Genome(), energy=0.01); plant.initialize(world.ground_y); world.occupy(1, plant.cells)
    plant.update(world, random.Random(1), 0, 0)
    assert not plant.alive


def test_reproducible_long_run_and_statistics():
    config = SimulationConfig(width=30, height=25, initial_plants=5, seed=3)
    first, second = Simulation(config), Simulation(config)
    for _ in range(200): first.step(); second.step()
    assert first.history == second.history
    assert first.snapshot().population == len(first.plants)


def test_default_environment_supports_multiple_generations():
    simulation = Simulation(SimulationConfig())
    for _ in range(400): simulation.step()
    assert simulation.snapshot().population > 0
    assert simulation.snapshot().generations > 0


def test_experiment_csv(tmp_path):
    path = run_experiments("stable", 2, 5, tmp_path / "runs.csv", SimulationConfig(width=20, height=20, initial_plants=3))
    assert len(path.read_text(encoding="utf-8").splitlines()) == 3
