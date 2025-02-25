import logging

from actionflow.action import Action

try:
    import docker as docker

    client = docker.from_env()
except ImportError:
    logging.error("Docker SDK not found")
    docker = None
    client = None


class ContainerAction(Action):
    """
    ContainerAction represents an action to be performed on a Docker container.
    """

    name: str = "container-action"
    description: str = "Container action"
    container: str
    commands: list[str]
    user: str = "odoo"
    tty: bool = False
    stream: bool = False
    workdir: str = "/var/lib/odoo/.local/upgrade"
    _buffer: str = ""

    @property
    def services(self):
        return self.context.services.list()

    def _check(self):
        try:
            client.containers.get(self.container)
        except docker.errors.NotFound:
            return False
        return True

    def _parse(self, chunk):
        print(chunk, end="")
        self._buffer += chunk

    def _run(self):
        container = client.containers.get(self.container)

        if not self.stream:
            for command in self.commands:
                try:
                    exec_result = container.exec_run(
                        command,
                        tty=self.tty,
                        user=self.user,
                        environment={"PIP_ROOT_USER_ACTION": "ignore"},
                        workdir=self.workdir,
                    )

                    logging.debug(
                        f"Running command '{command}' in container '{container.name}'"
                    )

                    logging.info(
                        "Command output:\n%s", exec_result.output.decode("utf-8")
                    )

                    assert exec_result.exit_code == 0, "Command failed"

                except Exception as e:
                    logging.error(f"Error while running command: {e}")
                    return False
        else:
            for command in self.commands:
                try:
                    # Run the command with streaming enabled
                    exec_id = container.client.api.exec_create(
                        container.id,
                        command,
                        tty=True,
                        workdir=self.workdir,
                        user=self.user,
                    )
                    output_stream = container.client.api.exec_start(
                        exec_id["Id"], stream=True
                    )

                    # Stream the output
                    # INFO source odoo.modules.loading: Loading module account_taxcloud (65/66)
                    print("Streaming command output:")
                    # addons = 0
                    for chunk in output_stream:
                        self._parse(chunk.decode("utf-8"))

                    #     if "Loading module" in line:
                    #         # Compile and use the regex to extract the required information
                    #         pattern = r": Loading module (\w+) \((\d+)/(\d+)\)"
                    #         match = re.search(pattern, line)
                    #         if match:
                    #             result = {
                    #                 "name": match.group(1),
                    #                 "index": int(match.group(2)),
                    #                 "total": int(match.group(3)),
                    #             }
                    #             print(result)
                    #             addons += 1

                    # print(f"Total addons: {addons}")
                    logging.info(self._buffer)

                except Exception as e:
                    logging.error(f"Error while running command: {e}")
                    return False

        return True
