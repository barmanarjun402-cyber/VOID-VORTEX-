from pathlib import Path

import docker
from docker.errors import DockerException

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ContainerService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = docker.DockerClient(base_url=settings.docker_socket)
        self.network = settings.docker_network

    def start_bot_container(
        self,
        bot_slug: str,
        deploy_path: Path,
        run_command: str,
        cpu_limit: int,
        ram_limit_mb: int,
    ) -> str:
        try:
            container = self.client.containers.run(
                image="python:3.11-slim",
                name=f"bot-{bot_slug}",
                command=["bash", "-lc", run_command],
                working_dir="/app",
                volumes={str(deploy_path): {"bind": "/app", "mode": "ro"}},
                network=self.network,
                detach=True,
                mem_limit=f"{ram_limit_mb}m",
                nano_cpus=cpu_limit * 1_000_000_000,
                restart_policy={"Name": "unless-stopped"},
                security_opt=["no-new-privileges"],
                cap_drop=["ALL"],
                pids_limit=256,
            )
            return container.id
        except DockerException as exc:
            logger.error("container_start_failed", error=str(exc), bot_slug=bot_slug)
            raise

    def stop_container(self, container_id: str) -> None:
        container = self.client.containers.get(container_id)
        container.stop(timeout=10)

    def restart_container(self, container_id: str) -> None:
        container = self.client.containers.get(container_id)
        container.restart(timeout=10)

    def remove_container(self, container_id: str) -> None:
        container = self.client.containers.get(container_id)
        container.remove(force=True)

    def container_stats(self, container_id: str) -> dict:
        container = self.client.containers.get(container_id)
        return container.stats(stream=False)
