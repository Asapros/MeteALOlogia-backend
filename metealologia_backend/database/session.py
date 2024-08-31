from metealologia_backend.database import Database
from metealologia_backend.config import settings
from importlib import import_module

loaded_module = import_module(".." + settings.database_flavour, __name__)
function = getattr(loaded_module, "instantiate", None)
if function is None:
    raise ImportError("Could not find 'instantiate' function inside loaded database module '{}'".format(loaded_module))
database: Database = function()

__all__ = ["database"]
