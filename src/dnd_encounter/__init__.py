# src/dnd_encounter/__init__.py

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("dnd-encounter-manager")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

