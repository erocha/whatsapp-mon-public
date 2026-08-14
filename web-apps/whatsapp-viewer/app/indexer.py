from __future__ import annotations

import argparse
import sqlite3
import time

from .config import load_settings
from .storage import fallback_name, initialize, name_map, readonly, viewer


def build(reset: bool = False, batch_size: int = 5000) -> None:
    settings = load_settings()
    initialize(settings)
    with viewer(settings) as target:
        if reset:
            target.execute("DELETE FROM message_fts")
            target.execute("DELETE FROM index_state WHERE key='last_message_id'")
        row = target.execute("SELECT value FROM index_state WHERE key='last_message_id'").fetchone()
        last_id = int(row[0]) if row else 0
    total = 0
    started = time.time()
    while True:
        with readonly(settings.msgstore) as source:
            rows = source.execute(
                """SELECT m._id,m.text_data,m.timestamp,m.chat_row_id,c.subject,j.raw_string jid,sj.raw_string sender_jid
                   FROM message m JOIN chat c ON c._id=m.chat_row_id JOIN jid j ON j._id=c.jid_row_id
                   LEFT JOIN jid sj ON sj._id=m.sender_jid_row_id
                   WHERE m._id>? AND m.text_data IS NOT NULL AND trim(m.text_data)<>''
                   ORDER BY m._id LIMIT ?""", (last_id, batch_size)
            ).fetchall()
        if not rows:
            break
        names = name_map(settings, [row["jid"] for row in rows] + [row["sender_jid"] for row in rows])
        payload = [(
            row["text_data"], names.get(row["sender_jid"]) or fallback_name(row["sender_jid"]),
            names.get(row["jid"]) or row["subject"] or fallback_name(row["jid"]), row["jid"],
            row["chat_row_id"], row["_id"], row["timestamp"]
        ) for row in rows]
        with viewer(settings) as target:
            target.executemany(
                "INSERT INTO message_fts(body,sender_name,chat_name,jid,chat_id,message_id,timestamp) VALUES(?,?,?,?,?,?,?)",
                payload,
            )
            last_id = int(rows[-1]["_id"])
            target.execute("INSERT INTO index_state(key,value) VALUES('last_message_id',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(last_id),))
        total += len(rows)
        elapsed = max(time.time() - started, 0.01)
        print(f"Indexadas {total:,} mensagens nesta execução ({total/elapsed:,.0f}/s), última ID {last_id}", flush=True)
    with viewer(settings) as target:
        target.execute("INSERT INTO index_state(key,value) VALUES('completed_at',unixepoch()) ON CONFLICT(key) DO UPDATE SET value=excluded.value")
        target.execute("PRAGMA optimize")
    print("Índice atualizado.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--batch-size", type=int, default=5000)
    args = parser.parse_args()
    build(args.reset, args.batch_size)


if __name__ == "__main__":
    main()
