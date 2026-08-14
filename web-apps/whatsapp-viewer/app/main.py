from __future__ import annotations

import csv
import io
import time
from pathlib import Path

import vobject
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .config import ROOT, load_settings
from .repository import (calls, chat_detail, chats, contact_photo, contact_profile,
                         contact_profile_for_chat, contact_profile_for_message,
                         export_contacts_vcf, media_path, messages, participants, search)
from .storage import initialize, normalize_phone, parse_contacts_csv, readonly, setting_get, setting_set, viewer


settings = load_settings()
secret = initialize(settings)
passwords = PasswordHasher()
app = FastAPI(title="Arquivo WhatsApp", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=secret, session_cookie="waview_session", max_age=60 * 60 * 12, same_site="strict", https_only=True)
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")
templates = Jinja2Templates(directory=ROOT / "app" / "templates")


def authenticated(request: Request) -> bool:
    return bool(request.session.get("authenticated"))


def require_auth(request: Request) -> None:
    if not authenticated(request):
        raise HTTPException(status_code=401, detail="Autenticação necessária")


def csrf(request: Request) -> str:
    token = request.session.get("csrf")
    if not token:
        import secrets
        token = secrets.token_urlsafe(24)
        request.session["csrf"] = token
    return token


def require_csrf(request: Request, token: str) -> None:
    if not token or token != request.session.get("csrf"):
        raise HTTPException(status_code=403, detail="Token inválido")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if authenticated(request):
        return RedirectResponse("/", 303)
    return templates.TemplateResponse(request, "login.html", {"configured": bool(setting_get(settings, "password_hash")), "csrf": csrf(request)})


@app.post("/login")
def login(request: Request, password: str = Form(...), csrf_token: str = Form(...)):
    require_csrf(request, csrf_token)
    stored = setting_get(settings, "password_hash")
    if not stored:
        if len(password) < 10:
            return templates.TemplateResponse(request, "login.html", {"configured": False, "csrf": csrf(request), "error": "Use pelo menos 10 caracteres."}, status_code=400)
        setting_set(settings, "password_hash", passwords.hash(password))
    else:
        try:
            passwords.verify(stored, password)
        except VerifyMismatchError:
            time.sleep(0.6)
            return templates.TemplateResponse(request, "login.html", {"configured": True, "csrf": csrf(request), "error": "Senha incorreta."}, status_code=401)
    request.session.clear()
    request.session["authenticated"] = True
    csrf(request)
    return RedirectResponse("/", 303)


@app.post("/logout")
def logout(request: Request, csrf_token: str = Form(...)):
    require_auth(request)
    require_csrf(request, csrf_token)
    request.session.clear()
    return RedirectResponse("/login", 303)


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    if not authenticated(request):
        return RedirectResponse("/login", 303)
    return templates.TemplateResponse(request, "index.html", {"csrf": csrf(request)})


@app.get("/api/chats")
def api_chats(request: Request, kind: str = "all", q: str = "", limit: int = 100, offset: int = 0):
    require_auth(request)
    return chats(settings, kind, q, limit, offset)


@app.get("/api/chats/{chat_id}")
def api_chat(request: Request, chat_id: int):
    require_auth(request)
    result = chat_detail(settings, chat_id)
    if not result:
        raise HTTPException(404)
    return result


@app.get("/api/chats/{chat_id}/messages")
def api_messages(request: Request, chat_id: int, before: int | None = None, limit: int = 100):
    require_auth(request)
    return messages(settings, chat_id, before, limit)


@app.get("/api/chats/{chat_id}/participants")
def api_participants(request: Request, chat_id: int):
    require_auth(request)
    return participants(settings, chat_id)


@app.get("/api/calls")
def api_calls(request: Request, limit: int = 100, offset: int = 0):
    require_auth(request)
    return calls(settings, limit, offset)


@app.get("/api/search")
def api_search(request: Request, q: str = Query(min_length=1), chat_id: int | None = None, limit: int = 100):
    require_auth(request)
    try:
        return search(settings, q, chat_id, limit)
    except Exception as exc:
        if "fts5" in str(exc).lower() or "syntax" in str(exc).lower():
            raise HTTPException(400, "Consulta de pesquisa inválida") from exc
        raise


@app.get("/api/contact-profile")
def api_contact_profile(request: Request, jid: str):
    require_auth(request)
    result = contact_profile(settings, jid)
    if not result:
        raise HTTPException(404)
    return result


@app.get("/api/chats/{chat_id}/contact-profile")
def api_chat_contact_profile(request: Request, chat_id: int):
    require_auth(request)
    result = contact_profile_for_chat(settings, chat_id)
    if not result:
        raise HTTPException(404)
    return result


@app.get("/api/messages/{message_id}/contact-profile")
def api_message_contact_profile(request: Request, message_id: int):
    require_auth(request)
    result = contact_profile_for_message(settings, message_id)
    if not result:
        raise HTTPException(404)
    return result


@app.get("/api/contact-photo")
def api_contact_photo(request: Request, jid: str):
    require_auth(request)
    content = contact_photo(settings, jid)
    if not content:
        raise HTTPException(404)
    return Response(content=content, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=3600"})


@app.get("/media/{message_id}")
def media(request: Request, message_id: int):
    require_auth(request)
    resolved = media_path(settings, message_id)
    if not resolved:
        raise HTTPException(404)
    path, mime = resolved
    return FileResponse(path, media_type=mime, filename=path.name if not (mime or "").startswith(("image/", "audio/", "video/")) else None)


@app.get("/api/settings")
def api_settings(request: Request):
    require_auth(request)
    with viewer(settings) as db:
        indexed = db.execute("SELECT value FROM index_state WHERE key='last_message_id'").fetchone()
        aliases = db.execute("SELECT count(1) FROM aliases").fetchone()[0]
        contacts = db.execute("SELECT count(1) FROM imported_contacts").fetchone()[0]
    return {"indexed_through": indexed[0] if indexed else "0", "aliases": aliases, "contacts": contacts}


@app.post("/api/aliases")
def save_alias(request: Request, jid: str = Form(...), name: str = Form(...), csrf_token: str = Form(...)):
    require_auth(request); require_csrf(request, csrf_token)
    if not jid.strip() or not name.strip():
        raise HTTPException(400)
    with viewer(settings) as db:
        db.execute("INSERT INTO aliases(jid,name) VALUES(?,?) ON CONFLICT(jid) DO UPDATE SET name=excluded.name,updated_at=unixepoch()", (jid.strip(), name.strip()))
    return {"ok": True}


@app.post("/api/import-vcf")
async def import_vcf(request: Request, file: UploadFile = File(...), csrf_token: str = Form(...)):
    require_auth(request); require_csrf(request, csrf_token)
    if not (file.filename or "").lower().endswith((".vcf", ".vcard")):
        raise HTTPException(400, "Envie um arquivo VCF")
    raw = await file.read(20 * 1024 * 1024 + 1)
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(413, "VCF maior que 20 MB")
    text = raw.decode("utf-8-sig", errors="replace")
    records: list[tuple[str, str]] = []
    for card in vobject.readComponents(text):
        name = getattr(getattr(card, "fn", None), "value", "").strip()
        for tel in card.contents.get("tel", []):
            phone = normalize_phone(str(tel.value))
            if name and phone:
                records.extend([(f"{phone}@s.whatsapp.net", name), (f"{phone}@lid", name)])
    with viewer(settings) as db:
        db.executemany("INSERT INTO imported_contacts(jid,name) VALUES(?,?) ON CONFLICT(jid) DO UPDATE SET name=excluded.name", records)
    return {"ok": True, "imported": len(records) // 2}


@app.post("/api/import-contacts-csv")
async def import_contacts_csv(request: Request, file: UploadFile = File(...), csrf_token: str = Form(...)):
    require_auth(request); require_csrf(request, csrf_token)
    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(400, "Envie um arquivo CSV")
    raw = await file.read(20 * 1024 * 1024 + 1)
    if len(raw) > 20 * 1024 * 1024:
        raise HTTPException(413, "CSV maior que 20 MB")
    try:
        decoded = raw.decode("utf-8-sig", errors="strict")
        contacts = parse_contacts_csv(decoded)
    except (UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc
    if not contacts:
        raise HTTPException(400, "Nenhum contato válido encontrado")
    phones = [str(contact["phone"]) for contact in contacts]
    lid_by_phone: dict[str, list[str]] = {}
    with readonly(settings.msgstore) as source:
        for start in range(0, len(phones), 700):
            chunk = phones[start:start + 700]
            jids = [f"{phone}@s.whatsapp.net" for phone in chunk]
            marks = ",".join("?" for _ in jids)
            sql = f"""SELECT phone.raw_string phone_jid,lid.raw_string lid_jid
                FROM jid phone JOIN jid_map jm ON jm.jid_row_id=phone._id
                JOIN jid lid ON lid._id=jm.lid_row_id WHERE phone.raw_string IN ({marks})"""
            for row in source.execute(sql, jids):
                phone = str(row["phone_jid"]).split("@", 1)[0]
                lid_by_phone.setdefault(phone, []).append(str(row["lid_jid"]))
    imported: list[tuple[str, str, str]] = []
    metadata: list[tuple[object, ...]] = []
    for contact in contacts:
        phone, name = str(contact["phone"]), str(contact["name"])
        imported.append((f"{phone}@s.whatsapp.net", name, "csv"))
        imported.extend((lid, name, "csv") for lid in lid_by_phone.get(phone, []))
        metadata.append((phone, name, contact["push_name"], contact["short_name"], contact["is_business"], "csv"))
    with viewer(settings) as db:
        db.executemany("""INSERT INTO imported_contacts(jid,name,source) VALUES(?,?,?)
            ON CONFLICT(jid) DO UPDATE SET name=excluded.name,source=excluded.source""", imported)
        db.executemany("""INSERT INTO contact_metadata(phone,name,push_name,short_name,is_business,source)
            VALUES(?,?,?,?,?,?) ON CONFLICT(phone) DO UPDATE SET name=excluded.name,
            push_name=excluded.push_name,short_name=excluded.short_name,
            is_business=excluded.is_business,source=excluded.source,updated_at=unixepoch()""", metadata)
    total_records = max(sum(1 for _ in csv.DictReader(io.StringIO(decoded), delimiter=";")), 0)
    return {"ok": True, "imported": len(contacts), "skipped": total_records - len(contacts), "linked_lids": sum(map(len, lid_by_phone.values()))}


@app.get("/api/export-vcf")
def export_vcf(request: Request, scope: str = "chats"):
    require_auth(request)
    if scope not in {"chats", "all"}:
        raise HTTPException(400, "Escopo inválido")
    content, count = export_contacts_vcf(settings, include_participants=scope == "all")
    filename = "whatsapp-todos-participantes.vcf" if scope == "all" else "whatsapp-conversas-diretas.vcf"
    return Response(
        content=content,
        media_type="text/vcard; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Contact-Count": str(count),
            "Cache-Control": "no-store",
        },
    )
