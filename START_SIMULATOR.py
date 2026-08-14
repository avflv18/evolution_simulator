"""Запуск симулятора двойным щелчком без терминала."""

from pathlib import Path
import os
import subprocess
import sys
from tkinter import Tk, messagebox


PROJECT_DIR = Path(__file__).resolve().parent
VENV_PYTHONW = PROJECT_DIR / "venv" / "Scripts" / "pythonw.exe"


def show_error(text: str) -> None:
    root = Tk()
    root.withdraw()
    messagebox.showerror("Не удалось запустить симулятор", text)
    root.destroy()


# Если окружение venv существует, перезапускаем этот же файл через него.
if VENV_PYTHONW.is_file() and os.environ.get("EVOLUTION_VENV_ACTIVE") != "1":
    environment = os.environ.copy()
    environment["EVOLUTION_VENV_ACTIVE"] = "1"
    subprocess.Popen([str(VENV_PYTHONW), str(Path(__file__).resolve())], cwd=PROJECT_DIR, env=environment)
    raise SystemExit

sys.path.insert(0, str(PROJECT_DIR / "src"))

try:
    import pygame  # noqa: F401
    from evolution_simulator.config import SimulationConfig
    from evolution_simulator.simulation import Simulation
    from evolution_simulator.ui import run

    config = SimulationConfig.from_json(PROJECT_DIR / "configs" / "default.json")
    run(Simulation(config))
except ModuleNotFoundError as error:
    show_error(
        "Не найдена библиотека pygame.\n\n"
        "Один раз установите зависимости командой:\n"
        "pip install -r requirements.txt\n\n"
        f"Техническая информация: {error}"
    )
except Exception as error:
    show_error(f"Произошла ошибка:\n\n{type(error).__name__}: {error}")
