import importlib
import pkgutil


def load_all_actions():
    package_name = "actionflow.actions"
    package = importlib.import_module(package_name)
    for _, module_name, is_pkg in pkgutil.iter_modules(package.__path__):
        if not is_pkg:
            importlib.import_module(f"{package_name}.{module_name}")
