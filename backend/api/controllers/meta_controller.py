from fastapi import APIRouter
import time
from pathlib import Path
from typing import Tuple
import yaml

router = APIRouter(prefix="", tags=["meta"])

# Record the start time when this module is imported
_start_time: float = time.time()

def _load_config() -> dict:
    """Load configuration from config.yml in the backend config directory."""
    config_path = Path(__file__).resolve().parents[3] / "config" / "config.yml"
    try:
        with open(config_path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception:
        return {}

def _get_version_info() -> Tuple[str, str]:
    """Retrieve version and environment information from the configuration."""
    cfg = _load_config()
    return cfg.get("version", "0.0.0"), cfg.get("env", "unknown")

@router.get("/health")
async def health() -> dict:
    """Return basic health information including uptime seconds."""
    uptime = int(time.time() - _start_time)
    return {
        "status": "ok",
        "uptime_seconds": uptime,
    }

@router.get("/version")
async def version() -> dict:
    """Return version and environment loaded from the config file."""
    version_str, env_str = _get_version_info()
    return {
        "version": version_str,
        "env": env_str,
    }
