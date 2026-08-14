from __future__ import annotations

import re
import secrets
import sqlite3
from pathlib import Path
from typing import Iterable

from .config import Settings


def readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=20)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def viewer(settings: Settings) -> sqlite3.Connection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(settings.viewer_db, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def initialize(settings: Settings) -> str:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    if not settings.secret_file.exists():
        settings.secret_file.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    with viewer(settings) as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS aliases(jid TEXT PRIMARY KEY, name TEXT NOT NULL, updated_at INTEGER NOT NULL DEFAULT (unixepoch()));
            CREATE TABLE IF NOT EXISTS imported_contacts(jid TEXT PRIMARY KEY, name TEXT NOT NULL, source TEXT NOT NULL DEFAULT 'vcf');
            CREATE TABLE IF NOT EXISTS contact_metadata(
                phone TEXT PRIMARY KEY, name TEXT NOT NULL, push_name TEXT,
                short_name TEXT, is_business INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'csv', updated_at INTEGER NOT NULL DEFAULT (unixepoch())
            );
            CREATE TABLE IF NOT EXISTS index_state(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE VIRTUAL TABLE IF NOT EXISTS message_fts USING fts5(
                body, sender_name, chat_name, jid UNINDEXED, chat_id UNINDEXED,
                message_id UNINDEXED, timestamp UNINDEXED, tokenize='unicode61 remove_diacritics 2'
            );
            CREATE INDEX IF NOT EXISTS idx_aliases_name ON aliases(name);
            CREATE INDEX IF NOT EXISTS idx_imported_contacts_name ON imported_contacts(name);
            """
        )
    return settings.secret_file.read_text(encoding="utf-8").strip()


def setting_get(settings: Settings, key: str) -> str | None:
    with viewer(settings) as db:
        row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row[0] if row else None


def setting_set(settings: Settings, key: str, value: str) -> None:
    with viewer(settings) as db:
        db.execute("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


def name_map(settings: Settings, jids: Iterable[str]) -> dict[str, str]:
    values = list(dict.fromkeys(j for j in jids if j))
    if not values:
        return {}
    result: dict[str, str] = {}
    with viewer(settings) as db:
        for start in range(0, len(values), 800):
            chunk = values[start:start + 800]
            marks = ",".join("?" for _ in chunk)
            rows = db.execute(
                f"""SELECT jid,name,priority FROM (
                    SELECT jid,name,2 priority FROM imported_contacts WHERE jid IN ({marks})
                    UNION ALL SELECT jid,name,1 priority FROM aliases WHERE jid IN ({marks})
                ) ORDER BY priority DESC""",
                chunk + chunk,
            )
            for row in rows:
                result[row["jid"]] = row["name"]
    return result


def normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value)


def fallback_name(jid: str | None) -> str:
    if not jid:
        return "Desconhecido"
    return jid.split("@", 1)[0]


def parse_contacts_csv(text: str) -> list[dict[str, str | int]]:
    import csv
    import io

    required = ["Phone", "Name", "PushName", "ShortName", "IsBusiness"]
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    headers = [str(header or "").strip() for header in (reader.fieldnames or [])]
    if headers != required:
        raise ValueError("Cabeçalho esperado: " + ";".join(required))
    contacts: dict[str, dict[str, str | int]] = {}
    for line, row in enumerate(reader, start=2):
        phone = normalize_phone(row.get("Phone") or "")
        if not (7 <= len(phone) <= 15):
            # Exports may contain internal entries such as Phone=0;WhatsApp.
            # They cannot become address-book contacts and are safely skipped.
            continue
        name = str(row.get("Name") or "").strip()
        push_name = str(row.get("PushName") or "").strip()
        short_name = str(row.get("ShortName") or "").strip()
        business_raw = str(row.get("IsBusiness") or "").strip().lower()
        if business_raw not in {"true", "false", "1", "0", "yes", "no", "sim", "não", "nao", ""}:
            raise ValueError(f"IsBusiness inválido na linha {line}")
        contacts[phone] = {
            "phone": phone, "name": name or push_name or short_name or phone,
            "push_name": push_name, "short_name": short_name,
            "is_business": int(business_raw in {"true", "1", "yes", "sim"}),
        }
    return list(contacts.values())
