import argparse
import json
from pathlib import Path
from .config import Settings
from .models import DiscoveryConfig
from .pipeline import audit_match, corpus_summary, discover, ingest
from .store import Store


def main():
    parser = argparse.ArgumentParser(description="KUKU source-grounded candidate discovery")
    parser.add_argument("command", choices=["ingest", "discover", "shortlist"])
    parser.add_argument("--provider", choices=["rules", "ollama"])
    parser.add_argument("--export", type=Path, help="Write a run manifest and summary JSON")
    args = parser.parse_args()
    settings = Settings.from_env()
    store = Store(settings.db_path)
    episodes = ingest(settings, store)
    report = {"corpus": corpus_summary(episodes), "audit": audit_match(episodes)}
    if args.command == "discover":
        report["run"] = discover(settings, store, episodes, args.provider or settings.provider, DiscoveryConfig())
    elif args.command == "shortlist":
        run = store.run()
        if not run:
            report["run"] = discover(settings, store, episodes, args.provider or settings.provider, DiscoveryConfig())
            run = report["run"]
        from .editorial import build_editorial_shortlist
        from .models import Candidate
        with store.connection() as db:
            rows = db.execute("SELECT payload FROM candidates WHERE run_id=?", (run["id"],)).fetchall()
        cands = [Candidate.model_validate_json(r[0]) for r in rows]
        ep_dict = {e.number: e for e in episodes}
        report["shortlist"] = build_editorial_shortlist(cands, ep_dict, max_picks=10)
    if args.export:
        args.export.parent.mkdir(parents=True, exist_ok=True)
        args.export.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if "run" in report and report["run"]["status"] != "complete":
        raise SystemExit(1)



if __name__ == "__main__":
    main()
