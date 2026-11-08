"""Versioned source snapshots and run-scoped results; never update screenplay files."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from .models import Episode, Candidate


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS sources (hash TEXT PRIMARY KEY, episode INTEGER, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS active_sources (episode INTEGER PRIMARY KEY, hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS candidates (run_id TEXT NOT NULL, id TEXT NOT NULL, episode INTEGER NOT NULL,
                    start_cs INTEGER NOT NULL, end_cs INTEGER NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(run_id,id));
                CREATE INDEX IF NOT EXISTS candidate_order ON candidates(run_id,episode,start_cs,end_cs,id);
                CREATE TABLE IF NOT EXISTS annotations (run_id TEXT NOT NULL, episode INTEGER NOT NULL, payload TEXT NOT NULL,
                    PRIMARY KEY(run_id,episode));
                CREATE TABLE IF NOT EXISTS semantic_cache (key TEXT PRIMARY KEY, payload TEXT NOT NULL);
            """)

    @contextmanager
    def connection(self):
        with sqlite3.connect(self.path, timeout=30) as db:
            db.row_factory = sqlite3.Row
            yield db

    def ingest(self, episodes: list[Episode]):
        with self.connection() as db:
            db.execute("DELETE FROM active_sources")
            for e in episodes:
                db.execute("INSERT OR IGNORE INTO sources VALUES (?,?,?)", (e.source_sha256, e.number, e.model_dump_json()))
                db.execute("INSERT INTO active_sources VALUES (?,?)", (e.number, e.source_sha256))

    def episodes(self, hashes: dict | None = None) -> list[Episode]:
        with self.connection() as db:
            if hashes is None:
                rows = db.execute("SELECT s.payload FROM sources s JOIN active_sources a ON s.hash=a.hash ORDER BY s.episode").fetchall()
            else:
                rows = [db.execute("SELECT payload FROM sources WHERE hash=?", (h,)).fetchone() for h in hashes.values()]
                if any(row is None for row in rows):
                    raise ValueError("Run source snapshot missing")
            return sorted([Episode.model_validate_json(r["payload"]) for r in rows], key=lambda e: e.number)

    def save_run(self, run):
        with self.connection() as db:
            db.execute("INSERT INTO runs VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status,payload=excluded.payload",
                (run["id"], run["created"], run["status"], json.dumps(run)))

    def run(self, run_id=None):
        with self.connection() as db:
            row = db.execute("SELECT payload FROM runs WHERE id=?", (run_id,)).fetchone() if run_id else db.execute(
                "SELECT payload FROM runs ORDER BY created DESC,id DESC LIMIT 1").fetchone()
            return json.loads(row[0]) if row else None

    def runs(self):
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT payload FROM runs ORDER BY created DESC,id DESC LIMIT 30")]

    def save_episode_results(self, run_id, episode, candidates, annotations):
        with self.connection() as db:
            db.execute("DELETE FROM candidates WHERE run_id=? AND episode=?", (run_id, episode))
            db.executemany("INSERT INTO candidates VALUES (?,?,?,?,?,?)", [(run_id, c.id, c.episode,
                c.segments[0].start_cs, c.segments[0].end_cs, c.model_dump_json()) for c in candidates])
            db.execute("INSERT OR REPLACE INTO annotations VALUES (?,?,?)", (run_id, episode, json.dumps(annotations)))

    def candidate_page(self, run_id, episode=None, approach=None, hook_timing=None,
                       has_cliffhanger=None, variant_group=None, offset=0, limit=50):
        clauses, args = ["run_id=?"], [run_id]
        if episode is not None:
            clauses.append("episode=?")
            args.append(episode)
        if approach:
            clauses.append("EXISTS (SELECT 1 FROM json_each(candidates.payload,'$.approaches') WHERE value=?)")
            args.append(approach)
        if hook_timing:
            clauses.append("json_extract(candidates.payload, '$.hook_timing')=?")
            args.append(hook_timing)
        if has_cliffhanger is True:
            clauses.append("json_array_length(candidates.payload, '$.cliffhanger_ids') > 0")
        elif has_cliffhanger is False:
            clauses.append("json_array_length(candidates.payload, '$.cliffhanger_ids') = 0")
        if variant_group:
            clauses.append("json_extract(candidates.payload, '$.variant_group')=?")
            args.append(variant_group)
        where = " AND ".join(clauses)
        with self.connection() as db:
            total = db.execute(f"SELECT count(*) FROM candidates WHERE {where}", args).fetchone()[0]
            rows = db.execute(f"SELECT payload FROM candidates WHERE {where} ORDER BY episode,start_cs,end_cs,id LIMIT ? OFFSET ?",
                [*args, limit, offset]).fetchall()
        return {"total": total, "offset": offset, "limit": limit, "items": [json.loads(r[0]) for r in rows]}

    def variant_groups(self, run_id, episode=None):
        clauses, args = ["run_id=?"], [run_id]
        if episode is not None:
            clauses.append("episode=?")
            args.append(episode)
        where = " AND ".join(clauses)
        with self.connection() as db:
            rows = db.execute(
                f"SELECT json_extract(payload, '$.variant_group') as grp, count(*) as cnt "
                f"FROM candidates WHERE {where} GROUP BY grp ORDER BY min(episode), min(start_cs)",
                args
            ).fetchall()
        return [{"group": r[0], "count": r[1]} for r in rows]


    def candidate(self, run_id, candidate_id):
        with self.connection() as db:
            row = db.execute("SELECT payload FROM candidates WHERE run_id=? AND id=?", (run_id, candidate_id)).fetchone()
        return Candidate.model_validate_json(row[0]) if row else None

    def annotations(self, run_id, episode):
        with self.connection() as db:
            row = db.execute("SELECT payload FROM annotations WHERE run_id=? AND episode=?", (run_id, episode)).fetchone()
        return json.loads(row[0]) if row else []

    def cache_get(self, key):
        with self.connection() as db:
            row = db.execute("SELECT payload FROM semantic_cache WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def cache_put(self, key, payload):
        with self.connection() as db:
            db.execute("INSERT OR REPLACE INTO semantic_cache VALUES (?,?)", (key, json.dumps(payload)))
