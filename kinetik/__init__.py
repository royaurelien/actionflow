import importlib
import pkgutil

from kinetik.actions.base import Action


def load_all_actions():
    package_name = "kinetik.actions"
    package = importlib.import_module(package_name)
    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        if not is_pkg:
            importlib.import_module(f"{package_name}.{module_name}")

    print(f"Loaded actions: {Action.list()}")
