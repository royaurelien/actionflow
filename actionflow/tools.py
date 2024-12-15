from datetime import datetime
from functools import wraps
from string import Template
from typing import Any, List

import yaml

from actionflow.settings import Environment


class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


def group_by(items: List[Any], key: str):
    result = []  # Liste des groupes
    current_group = []  # Groupe en cours de construction

    for item in items:
        if getattr(item, key) is False:
            # Ajouter False au groupe en cours s'il existe
            if current_group:
                if getattr(current_group[-1], key) is False:
                    current_group.append(item)
                else:
                    result.append(current_group)
                    current_group = [item]
            else:
                current_group = [item]
        elif getattr(item, key) is True:
            # Si un groupe est en cours, le finaliser et commencer un nouveau groupe
            if current_group:
                if getattr(current_group[-1], key) is False:
                    current_group.append(item)
                    result.append(current_group)
                    current_group = []
                else:
                    result.append(current_group)
                    current_group = [item]
            else:
                current_group = [item]

    # Ajouter le dernier groupe s'il existe
    if current_group:
        result.append(current_group)

    return result


def update(fieldnames: str):
    def decorator_repeat(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            value = func(*args, **kwargs)
            self = args[0]

            obj = self
            attrs = fieldnames.split(".")
            for attr in attrs[:-1]:
                obj = getattr(obj, attr)
            setattr(obj, attrs[-1], datetime.now())

            return value

        return wrapper

    return decorator_repeat


def load_yaml_with_context(raw: str, context: dict = {}) -> dict:
    # Substitute environment and context variables using string.Template
    template = Template(raw)
    env = Environment()

    substituted_yaml = template.safe_substitute({**context, **env.model_dump()})
    # Parse the substituted YAML
    return yaml.safe_load(substituted_yaml)
