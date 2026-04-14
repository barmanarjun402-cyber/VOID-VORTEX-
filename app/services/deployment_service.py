import shutil
import subprocess
import zipfile
from pathlib import Path

from slugify import slugify

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.validator_service import ValidatorService

logger = get_logger(__name__)


class DeploymentService:
    def __init__(self):
        self.settings = get_settings()

    def clone_repo(self, repo_url: str, branch: str, destination: Path) -> None:
        if not ValidatorService.validate_github_repo(repo_url):
            raise ValueError("Invalid GitHub repository URL")
        destination.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(destination)]
        logger.info("clone_repo", cmd=" ".join(cmd))
        subprocess.run(cmd, check=True, timeout=self.settings.github_clone_timeout)

    def extract_zip(self, zip_path: Path, destination: Path) -> None:
        ValidatorService.validate_zip(zip_path)
        destination.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as zip_ref:
            zip_ref.extractall(destination)

    def detect_language(self, source_path: Path) -> str:
        if (source_path / "requirements.txt").exists() or any(source_path.glob("*.py")):
            return "python"
        if (source_path / "package.json").exists():
            return "node"
        if (source_path / "go.mod").exists():
            return "go"
        return "unknown"

    def detect_run_command(self, source_path: Path, language: str) -> str:
        if language == "python":
            if (source_path / "main.py").exists():
                return "pip install -r requirements.txt && python main.py"
            entrypoints = list(source_path.glob("*.py"))
            if entrypoints:
                return f"pip install -r requirements.txt && python {entrypoints[0].name}"
        if language == "node":
            return "npm ci && npm start"
        if language == "go":
            return "go mod download && go run ."
        raise ValueError("Could not determine run command")

    def prepare_source_dir(self, bot_name: str) -> tuple[str, Path]:
        slug = slugify(bot_name)
        path = self.settings.deploy_root / slug
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
        return slug, path
