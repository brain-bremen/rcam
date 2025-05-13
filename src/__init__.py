import toml
from pathlib import Path

version = toml.load(Path(__file__).parent / "pyproject.toml")["project"]["version"]
