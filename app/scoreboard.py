import json
import os
from datetime import datetime

LEADERBOARD_FILE = "leaderboard.json"


def _read_all_scores():
    """Return the full list of saved scores (may be empty)."""
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def _write_all_scores(scores):
    """Write the full list of scores back to disk."""
    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


def _parse_iso(ts: str):
    """Parse 'YYYY-MM-DDTHH:MM:SSZ' or ISO with offset; return datetime or None."""
    if not isinstance(ts, str):
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except Exception:
        return None


def _aggregate_best_per_player(scores):
    """
    Aggregate to one row per player:
      - Best score per player
      - Timestamp = player's latest game time (not necessarily the time of best score)
    """
    latest_ts_by_name = {}
    best_entry_by_name = {}

    for e in scores:
        name = e.get("name", "Unknown")
        score = e.get("score", 0)
        ts = e.get("timestamp")

        # Track latest timestamp overall for this player
        new_dt = _parse_iso(ts)
        cur_dt = _parse_iso(latest_ts_by_name.get(name)) if latest_ts_by_name.get(name) else None
        if cur_dt is None or (new_dt and new_dt > cur_dt):
            latest_ts_by_name[name] = ts

        # Track best score entry (tie-break by newer ts)
        best = best_entry_by_name.get(name)
        if best is None:
            best_entry_by_name[name] = dict(e)
        else:
            best_score = best.get("score", 0)
            if score > best_score:
                best_entry_by_name[name] = dict(e)
            elif score == best_score:
                best_dt = _parse_iso(best.get("timestamp"))
                if new_dt and (best_dt is None or new_dt > best_dt):
                    best_entry_by_name[name] = dict(e)

    fused = []
    for name, entry in best_entry_by_name.items():
        row = dict(entry)
        row["timestamp"] = latest_ts_by_name.get(name, entry.get("timestamp"))
        fused.append(row)

    return fused


def get_leaderboard(mode=None, top_n=10):
    """
    Return leaderboard entries:
      - Filter by mode ('solo' or 'multi') if provided; otherwise include all
      - Aggregate to best-per-player
      - Sort by score desc
      - Slice to top_n
    Underlying file keeps ALL entries.
    """
    scores = _read_all_scores()

    if mode in ("solo", "multi"):
        scores = [e for e in scores if e.get("mode") == mode]

    fused = _aggregate_best_per_player(scores)
    fused.sort(key=lambda e: e.get("score", 0), reverse=True)
    return fused[:top_n]


def save_score(name, score, meta=None):
    """
    Append a new score to the persistent store, keeping ALL entries.
    `meta` can include extra info, e.g. {"mode": "solo"/"multi", "customers": ..., ...}.
    """
    scores = _read_all_scores()
    entry = {
        "name": name,
        "score": score,
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z",
    }
    if isinstance(meta, dict):
        entry.update(meta)

    scores.append(entry)
    _write_all_scores(scores)
