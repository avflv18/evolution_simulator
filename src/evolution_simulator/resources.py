import math


def season_factors(tick: int, season_length: int) -> tuple[float, float, str]:
    phase = (tick % season_length) / season_length
    light = 0.7 + 0.3 * math.sin(math.tau * phase)
    rain = 0.75 + 0.25 * math.sin(math.tau * phase + math.pi / 2)
    names = ("весна", "лето", "осень", "зима")
    return max(0.35, light), max(0.35, rain), names[int(phase * 4) % 4]
