import re
import zipfile
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)

GITHUB_RE = re.compile(r"^https://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+/?$")
FORBIDDEN_PATTERNS = [
    re.compile(r"(?i)telegram[_-]?bot[_-]?token\s*=\s*['\"]\d+:[A-Za-z0-9_-]{30,}['\"]"),
    re.compile(r"(?i)api[_-]?key\s*=\s*['\"][A-Za-z0-9_-]{20,}['\"]"),
]


class ValidatorService:
    @staticmethod
    def validate_github_repo(url: str) -> bool:
        return bool(GITHUB_RE.match(url))

    @staticmethod
    def sanitize_name(name: str) -> str:
        cleaned = re.sub(r"[^a-zA-Z0-9-_ ]", "", name).strip()
        return cleaned[:80]

    @staticmethod
    def scan_token_leaks(path: Path) -> list[str]:
        findings: list[str] = []
        for file_path in path.rglob("*"):
            if not file_path.is_file() or file_path.stat().st_size > 5_000_000:
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pattern in FORBIDDEN_PATTERNS:
                if pattern.search(content):
                    findings.append(str(file_path))
                    break
        return findings

    @staticmethod
    def validate_zip(path: Path) -> None:
        with zipfile.ZipFile(path) as zip_ref:
            names = zip_ref.namelist()
            if len(names) > 2000:
                raise ValueError("Zip contains too many files")
            for name in names:
                if name.startswith("/") or ".." in Path(name).parts:
                    raise ValueError("Invalid zip entry path traversal")
