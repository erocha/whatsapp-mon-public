from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .config import Settings
from .storage import fallback_name, name_map, readonly, viewer


def phone_label(phone: str | None) -> str | None:
    return f"+{phone}" if phone and phone.isdigit() else None


def display_name(name: str, phone: str | None) -> str:
    label = phone_label(phone)
    if not label:
        return name
    if name.lstrip("+") == phone:
        return label
    return f"{name} · {label}"


def _phone_map(settings: Settings, jids: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    lids: list[str] = []
    for jid in dict.fromkeys(jids):
        user, separator, server = jid.partition("@")
        if separator and server == "s.whatsapp.net" and user.isdigit():
            result[jid] = user
        elif separator and server == "lid":
            lids.append(jid)
    if lids:
        with readonly(settings.msgstore) as db:
            for start in range(0, len(lids), 800):
                chunk = lids[start:start + 800]
                marks = ",".join("?" for _ in chunk)
                sql = f"""SELECT lid.raw_string lid,phone.raw_string phone
                    FROM jid lid JOIN jid_map jm ON jm.lid_row_id=lid._id
                    JOIN jid phone ON phone._id=jm.jid_row_id
                    WHERE lid.raw_string IN ({marks})"""
                for row in db.execute(sql, chunk):
                    phone = str(row["phone"] or "").split("@", 1)[0]
                    if phone.isdigit():
                        result[str(row["lid"])] = phone
    return result


def _decorate_names(settings: Settings, rows: list[dict[str, Any]], jid_key: str = "jid") -> list[dict[str, Any]]:
    jids = [str(row.get(jid_key) or "") for row in rows]
    names = name_map(settings, jids)
    phones = _phone_map(settings, jids)
    for row in rows:
        jid = str(row.get(jid_key) or "")
        phone = phones.get(jid)
        row["phone"] = phone
        base_name = names.get(jid) or row.get("subject") or fallback_name(jid)
        row["name"] = display_name(base_name, phone)
    return rows


def chats(settings: Settings, kind: str = "all", query: str = "", limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    clauses = ["j.raw_string IS NOT NULL", "c.last_message_row_id IS NOT NULL"]
    params: list[Any] = []
    if kind == "groups":
        clauses.append("j.server='g.us'")
    elif kind == "contacts":
        clauses.append("j.server IN ('s.whatsapp.net','lid')")
    elif kind == "channels":
        clauses.append("j.server='newsletter'")
    if query:
        clauses.append("(c.subject LIKE ? OR j.raw_string LIKE ?)")
        params.extend([f"%{query}%", f"%{query}%"])
    params.extend([min(limit, 200), max(offset, 0)])
    sql = f"""
        SELECT c._id chat_id,j.raw_string jid,c.subject,c.sort_timestamp,c.archived,c.group_member_count,
               m.text_data preview,m.message_type,m.timestamp last_timestamp
        FROM chat c JOIN jid j ON j._id=c.jid_row_id
        LEFT JOIN message m ON m._id=c.last_message_row_id
        WHERE {' AND '.join(clauses)} ORDER BY c.sort_timestamp DESC LIMIT ? OFFSET ?
    """
    with readonly(settings.msgstore) as db:
        rows = [dict(row) for row in db.execute(sql, params)]
    return _decorate_names(settings, rows)


def chat_detail(settings: Settings, chat_id: int) -> dict[str, Any] | None:
    with readonly(settings.msgstore) as db:
        row = db.execute(
            """SELECT c._id chat_id,j.raw_string jid,c.subject,c.created_timestamp,c.group_member_count,c.archived
               FROM chat c JOIN jid j ON j._id=c.jid_row_id WHERE c._id=?""", (chat_id,)
        ).fetchone()
    if not row:
        return None
    result = dict(row)
    _decorate_names(settings, [result])
    return result


def messages(settings: Settings, chat_id: int, before: int | None = None, limit: int = 100) -> list[dict[str, Any]]:
    params: list[Any] = [chat_id]
    cursor = ""
    if before:
        cursor = "AND m.sort_id < ?"
        params.append(before)
    params.append(min(limit, 200))
    sql = f"""
        SELECT m._id message_id,m.sort_id,m.from_me,m.timestamp,m.message_type,m.text_data,m.status,m.starred,
               sj.raw_string sender_jid,mm.mime_type,mm.file_path,mm.media_name,mm.media_caption,mm.media_duration,
               mm.width,mm.height,mm.raw_transcription_text,
               mq.text_data quoted_text,mq.from_me quoted_from_me
        FROM message m
        LEFT JOIN jid sj ON sj._id=m.sender_jid_row_id
        LEFT JOIN message_media mm ON mm.message_row_id=m._id
        LEFT JOIN message_quoted mq ON mq.message_row_id=m._id
        WHERE m.chat_row_id=? {cursor}
        ORDER BY m.sort_id DESC LIMIT ?
    """
    with readonly(settings.msgstore) as db:
        rows = [dict(row) for row in db.execute(sql, params)]
        ids = [row["message_id"] for row in rows]
        reactions: dict[int, list[dict[str, Any]]] = {}
        if ids:
            for start in range(0, len(ids), 800):
                chunk = ids[start:start + 800]
                marks = ",".join("?" for _ in chunk)
                reaction_sql = f"""SELECT a.parent_message_row_id message_id,r.reaction,j.raw_string sender_jid
                    FROM message_add_on a JOIN message_add_on_reaction r ON r.message_add_on_row_id=a._id
                    LEFT JOIN jid j ON j._id=a.sender_jid_row_id WHERE a.parent_message_row_id IN ({marks})"""
                for reaction in db.execute(reaction_sql, chunk):
                    reactions.setdefault(reaction["message_id"], []).append(dict(reaction))
    sender_jids = [str(row.get("sender_jid") or "") for row in rows]
    names = name_map(settings, sender_jids)
    phones = _phone_map(settings, sender_jids)
    for row in rows:
        sender_jid = str(row.get("sender_jid") or "")
        row["sender_phone"] = phones.get(sender_jid)
        base_name = names.get(sender_jid) or fallback_name(row.get("sender_jid"))
        row["sender_name"] = display_name(base_name, row["sender_phone"])
        row["reactions"] = reactions.get(row["message_id"], [])
        if row.get("file_path"):
            relative = media_relative_path(row["file_path"])
            candidate = (settings.media / relative).resolve()
            try:
                candidate.relative_to(settings.media.resolve())
                row["media_available"] = candidate.is_file()
            except ValueError:
                row["media_available"] = False
            if not row["media_available"]:
                row["file_path"] = None
    rows.reverse()
    return rows


def participants(settings: Settings, chat_id: int) -> list[dict[str, Any]]:
    with readonly(settings.msgstore) as db:
        chat = db.execute("SELECT jid_row_id FROM chat WHERE _id=?", (chat_id,)).fetchone()
        if not chat:
            return []
        rows = [dict(row) for row in db.execute(
            """SELECT j.raw_string jid,g.rank,g.pending,g.add_timestamp,g.label
               FROM group_participant_user g JOIN jid j ON j._id=g.user_jid_row_id
               WHERE g.group_jid_row_id=? ORDER BY g.rank DESC,j.raw_string""", (chat[0],)
        )]
    return _decorate_names(settings, rows)


def calls(settings: Settings, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    with readonly(settings.msgstore) as db:
        rows = [dict(row) for row in db.execute(
            """SELECT cl._id,cl.timestamp,cl.duration,cl.video_call,cl.from_me,cl.call_result,
                      COALESCE(gj.raw_string,j.raw_string) jid
               FROM call_log cl LEFT JOIN jid j ON j._id=cl.jid_row_id
               LEFT JOIN jid gj ON gj._id=cl.group_jid_row_id
               ORDER BY cl.timestamp DESC LIMIT ? OFFSET ?""", (min(limit, 200), max(offset, 0))
        )]
    return _decorate_names(settings, rows)


def search(settings: Settings, query: str, chat_id: int | None = None, limit: int = 100) -> list[dict[str, Any]]:
    if not query.strip():
        return []
    clause = "message_fts MATCH ?"
    params: list[Any] = [query.replace('"', '""')]
    if chat_id is not None:
        clause += " AND chat_id=?"
        params.append(chat_id)
    params.append(min(limit, 200))
    with viewer(settings) as db:
        rows = [dict(row) for row in db.execute(
            f"""SELECT message_id,chat_id,jid,chat_name,sender_name,
                snippet(message_fts,0,'<mark>','</mark>','…',24) snippet,timestamp
                FROM message_fts WHERE {clause} ORDER BY rank LIMIT ?""", params
        )]
    return rows


def media_relative_path(file_path: str) -> Path:
    """Turn Android/WhatsApp media paths into paths relative to Media."""
    raw = str(file_path).replace("\\", "/").lstrip("/")
    lowered = raw.lower()
    markers = ("whatsapp/media/", "media/")
    for marker in markers:
        position = lowered.find(marker)
        if position >= 0:
            raw = raw[position + len(marker):]
            break
    return Path(*[part for part in raw.split("/") if part])


def media_path(settings: Settings, message_id: int) -> tuple[Path, str | None] | None:
    with readonly(settings.msgstore) as db:
        row = db.execute("SELECT file_path,mime_type FROM message_media WHERE message_row_id=?", (message_id,)).fetchone()
    if not row or not row[0]:
        return None
    relative = media_relative_path(row[0])
    candidate = (settings.media / relative).resolve()
    root = settings.media.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return (candidate, row[1]) if candidate.is_file() else None


def vcard_escape(value: str) -> str:
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace(";", "\\;").replace(",", "\\,")


def export_contacts_vcf(settings: Settings, include_participants: bool = False) -> tuple[str, int]:
    """Export phone-number JIDs; opaque LIDs cannot be converted to contacts."""
    with readonly(settings.msgstore) as db:
        if include_participants:
            rows = db.execute(
                """SELECT DISTINCT raw_string jid FROM jid
                   WHERE server='s.whatsapp.net' AND raw_string IS NOT NULL
                   ORDER BY raw_string"""
            ).fetchall()
        else:
            rows = db.execute(
                """SELECT DISTINCT j.raw_string jid
                   FROM chat c JOIN jid j ON j._id=c.jid_row_id
                   WHERE j.server='s.whatsapp.net' AND j.raw_string IS NOT NULL
                   ORDER BY j.raw_string"""
            ).fetchall()
    contacts: list[tuple[str, str]] = []
    for row in rows:
        jid = str(row["jid"])
        phone = jid.split("@", 1)[0]
        if phone.isdigit() and 7 <= len(phone) <= 15:
            contacts.append((jid, phone))
    names = name_map(settings, [jid for jid, _ in contacts])
    cards: list[str] = []
    for jid, phone in contacts:
        name = names.get(jid) or phone
        cards.extend(("BEGIN:VCARD", "VERSION:3.0", f"FN:{vcard_escape(name)}",
                      f"TEL;TYPE=CELL:+{phone}", f"X-WHATSAPP-JID:{jid}", "END:VCARD"))
    return "\r\n".join(cards) + ("\r\n" if cards else ""), len(contacts)


def _equivalent_jids(db: sqlite3.Connection, jid: str) -> list[sqlite3.Row]:
    row = db.execute("SELECT _id,raw_string FROM jid WHERE raw_string=?", (jid,)).fetchone()
    if not row:
        return []
    ids = {int(row["_id"])}
    for mapped in db.execute(
        "SELECT lid_row_id,jid_row_id FROM jid_map WHERE lid_row_id=? OR jid_row_id=?",
        (row["_id"], row["_id"]),
    ):
        ids.update((int(mapped["lid_row_id"]), int(mapped["jid_row_id"])))
    marks = ",".join("?" for _ in ids)
    return db.execute(f"SELECT _id,raw_string,server FROM jid WHERE _id IN ({marks})", tuple(ids)).fetchall()


def contact_profile(settings: Settings, jid: str, preferred_chat_id: int | None = None) -> dict[str, Any] | None:
    with readonly(settings.msgstore) as db:
        equivalents = _equivalent_jids(db, jid)
        if not equivalents:
            return None
        equivalent_ids = [int(row["_id"]) for row in equivalents]
        equivalent_raw = [str(row["raw_string"]) for row in equivalents]
        phone = next((raw.split("@", 1)[0] for raw in equivalent_raw if raw.endswith("@s.whatsapp.net")), None)
        marks = ",".join("?" for _ in equivalent_ids)
        direct_chat = None
        if preferred_chat_id:
            direct_chat = db.execute("SELECT _id FROM chat WHERE _id=?", (preferred_chat_id,)).fetchone()
        if not direct_chat:
            direct_chat = db.execute(
                f"SELECT _id FROM chat WHERE jid_row_id IN ({marks}) ORDER BY sort_timestamp DESC LIMIT 1",
                equivalent_ids,
            ).fetchone()
        direct_chat_id = int(direct_chat[0]) if direct_chat else None
        groups = [dict(row) for row in db.execute(
            f"""SELECT DISTINCT c._id chat_id,gj.raw_string jid,c.subject,c.group_member_count
                FROM group_participant_user gpu
                JOIN chat c ON c.jid_row_id=gpu.group_jid_row_id
                JOIN jid gj ON gj._id=gpu.group_jid_row_id
                WHERE gpu.user_jid_row_id IN ({marks})
                ORDER BY c.sort_timestamp DESC LIMIT 200""",
            equivalent_ids,
        )]
        media: list[dict[str, Any]] = []
        media_count = 0
        has_photo = False
        if direct_chat_id:
            media_count = int(db.execute(
                "SELECT count(*) FROM message_media WHERE chat_row_id=? AND file_path IS NOT NULL",
                (direct_chat_id,),
            ).fetchone()[0])
            media = [dict(row) for row in db.execute(
                """SELECT message_row_id message_id,mime_type,media_name
                   FROM message_media WHERE chat_row_id=? AND file_path IS NOT NULL
                   ORDER BY message_row_id DESC LIMIT 12""",
                (direct_chat_id,),
            )]
            has_photo = bool(db.execute(
                """SELECT 1 FROM message_system_photo_change pc JOIN message m ON m._id=pc.message_row_id
                   WHERE m.chat_row_id=? AND pc.new_photo IS NOT NULL ORDER BY m.sort_id DESC LIMIT 1""",
                (direct_chat_id,),
            ).fetchone())
    stored_names = name_map(settings, equivalent_raw)
    base_name = next((stored_names.get(raw) for raw in equivalent_raw if stored_names.get(raw)), None)
    if not base_name:
        base_name = phone or fallback_name(jid)
    metadata: dict[str, Any] = {}
    if phone:
        with viewer(settings) as local_db:
            metadata_row = local_db.execute(
                "SELECT push_name,short_name,is_business,source FROM contact_metadata WHERE phone=?", (phone,)
            ).fetchone()
            if metadata_row:
                metadata = dict(metadata_row)
    return {
        "jid": jid, "equivalent_jids": equivalent_raw, "phone": phone,
        "name": base_name, "direct_chat_id": direct_chat_id,
        "groups": groups, "group_count": len(groups), "media": media,
        "media_count": media_count, "has_photo": has_photo, **metadata,
    }


def contact_profile_for_chat(settings: Settings, chat_id: int) -> dict[str, Any] | None:
    with readonly(settings.msgstore) as db:
        row = db.execute("SELECT j.raw_string FROM chat c JOIN jid j ON j._id=c.jid_row_id WHERE c._id=?", (chat_id,)).fetchone()
    return contact_profile(settings, str(row[0]), chat_id) if row else None


def contact_profile_for_message(settings: Settings, message_id: int) -> dict[str, Any] | None:
    with readonly(settings.msgstore) as db:
        row = db.execute(
            """SELECT j.raw_string,m.chat_row_id FROM message m
               JOIN jid j ON j._id=m.sender_jid_row_id WHERE m._id=?""", (message_id,)
        ).fetchone()
    return contact_profile(settings, str(row[0])) if row else None


def contact_photo(settings: Settings, jid: str) -> bytes | None:
    with readonly(settings.msgstore) as db:
        equivalents = _equivalent_jids(db, jid)
        if not equivalents:
            return None
        ids = [int(row["_id"]) for row in equivalents]
        marks = ",".join("?" for _ in ids)
        row = db.execute(
            f"""SELECT pc.new_photo FROM message_system_photo_change pc
                JOIN message m ON m._id=pc.message_row_id JOIN chat c ON c._id=m.chat_row_id
                WHERE c.jid_row_id IN ({marks}) AND pc.new_photo IS NOT NULL
                ORDER BY m.sort_id DESC LIMIT 1""", ids
        ).fetchone()
    return bytes(row[0]) if row else None
