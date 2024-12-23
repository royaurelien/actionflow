import logging
from typing import List

from actionflow.action import Action
from actionflow.models import ImageSchema

try:
    import docker as docker

    client = docker.from_env()
except ImportError:
    logging.error("Docker SDK not found")
    docker = None
    client = None


class Pull(Action):
    """
    Action to pull Docker images.

    Attributes:
        name (str): The name of the action, default is "pull".
        description (str): A brief description of the action, default is "Pull docker images".
        registry (str): The Docker registry to pull images from.
        login (str): The login username for the Docker registry.
        password (str): The login password for the Docker registry.
        images (List[ImageSchema]): A list of images to be pulled, defined by the ImageSchema.

    Methods:
        _get_credentials() -> dict:
            Retrieves the credentials for Docker registry authentication.

        _check() -> bool:
            Checks if all specified images are already present in the local Docker client.

        _run() -> bool:
            Pulls the specified images from the Docker registry if they are not already present.
    """

    name: str = "pull"
    description: str = "Pull docker images"

    registry: str = None
    login: str = None
    password: str = None
    images: List[ImageSchema]

    def _get_credentials(self) -> dict:
        vals = {"registry": self.registry} if self.registry else {}
        if self.login and self.password:
            vals.update({"username": self.login, "password": self.password})

        return {"auth_config": vals}

    def _check(self) -> bool:
        try:
            return all(client.images.get(image.name) for image in self.images)
        except docker.errors.ImageNotFound:
            return False

    def _run(self) -> bool:
        for image in self.images:
            try:
                client.images.get(image.name)
            except docker.errors.ImageNotFound:
                logging.info(f"Image {image.name} not found")

                client.images.pull(repository=image.repository, tag=image.tag)
                logging.info(f"Image {image.name} pulled")
            else:
                logging.info(f"Image {image.name} already exists")
        return True
