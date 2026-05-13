from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_env() -> None:
    for candidate in (PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.local"):
        if candidate.exists():
            load_dotenv(candidate, override=True)


def project_path(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)
