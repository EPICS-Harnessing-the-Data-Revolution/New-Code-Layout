from importlib import import_module
from pathlib import Path
import pkgutil
import logging

"""
Package: datasources

Auto-imports all non-private modules in this package so implementations
can be discovered via `from services.backend.datasources import <module>`.
"""


logger = logging.getLogger(__name__)

__all__ = []

_package = __package__ or Path(__file__).stem  # fallback for some import contexts
_package_dir = Path(__file__).resolve().parent

for _finder, _name, _ispkg in pkgutil.iter_modules([str(_package_dir)]):
    if _name.startswith("_"):
        continue
    try:
        import_module(f"{__package__}.{_name}")
        __all__.append(_name)
    except Exception:
        logger.exception("Failed to import datasource module %s", _name)