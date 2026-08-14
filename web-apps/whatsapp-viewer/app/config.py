from __future__ import annotations

import os
import socket
import tomllib
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    msgstore: Path
    contacts: Path
    media: Path
    data_dir: Path
    host: str = "127.0.0.1"
    port: int = 8765

    @property
    def viewer_db(self) -> Path:
        return self.data_dir / "viewer-data.db"

    @property
    def secret_file(self) -> Path:
        return self.data_dir / "session-secret.txt"


def load_settings() -> Settings:
    config_path = Path(os.environ.get("WAVIEW_CONFIG", ROOT / "config.toml"))
    if not config_path.exists():
        config_path = ROOT / "config.toml.example"
    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)
    data_dir = Path(raw.get("data_dir", "data"))
    if not data_dir.is_absolute():
        data_dir = ROOT / data_dir
    return Settings(
        msgstore=Path(raw["msgstore"]),
        contacts=Path(raw["contacts"]),
        media=Path(raw["media"]),
        data_dir=data_dir,
        host=str(raw.get("host", "127.0.0.1")),
        port=int(raw.get("port", 8765)),
    )


def local_names() -> list[str]:
    names = {"localhost", "127.0.0.1", socket.gethostname(), f"{socket.gethostname()}.local"}
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = item[4][0]
            if not address.startswith("127."):
                names.add(address)
    except OSError:
        pass
    return sorted(names)
