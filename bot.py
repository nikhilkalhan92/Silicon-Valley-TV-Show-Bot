import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from auth import get_api

# Silicon Valley episode counts per season
SEASONS = [8, 10, 10, 10, 8, 7]

def load_state(state_path: Path):
    if not state_path.exists():
        return {"season": 1, "episode": 1, "line": 0}
    return json.loads(state_path.read_text(encoding="utf-8", errors="ignore"))

def save_state(state_path: Path, state: dict):
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

def episode_path(scripts_root: Path, season: int, episode: int) -> Path:
    return scripts_root / str(season) / str(episode) / f"{episode}.txt"

def read_episode_lines(path: Path):
    lines = [l.strip() for l in path.read_text(encoding="utf-8", errors="ignore").splitlines()]
    return [l for l in lines if l]

def bump_episode(season: int, episode: int):
    episode += 1
    if episode > SEASONS[season - 1]:
        episode = 1
        season += 1
        if season > len(SEASONS):
            season = 1
    return season, episode

def split_chunks(text: str, max_len: int = 270):
    text = text.strip()
    if len(text) <= max_len:
        return [text]
    chunks = []
    while len(text) > max_len:
        cut = text.rfind(" ", 0, max_len)
        if cut == -1:
            cut = max_len
        chunks.append(text[:cut].strip() + "…")
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks

def post(api, text: str, dry_run: bool):
    chunks = split_chunks(text)

    if dry_run:
        print("[DRY_RUN] Would post:")
        for i, c in enumerate(chunks, 1):
            print(f"  ({i}/{len(chunks)}) {c}")
        return

    reply_to = None
    for c in chunks:
        if reply_to is None:
            status = api.update_status(c)
        else:
            status = api.update_status(
                c,
                in_reply_to_status_id=reply_to,
                auto_populate_reply_metadata=True
            )
        reply_to = status.id

def run(mode: str):
    load_dotenv()

    scripts_root = Path(os.getenv("SCRIPTS_ROOT", "./scripts")).resolve()
    state_path = Path(os.getenv("STATE_PATH", "./state/cur.json")).resolve()
    interval = int(os.getenv("TWEET_INTERVAL_SECS", "5400"))
    dry_run = os.getenv("DRY_RUN", "true").lower() == "true"

    api = None if dry_run else get_api()
    state = load_state(state_path)

    while True:
        season = state["season"]
        episode = state["episode"]
        line_idx = state["line"]

        ep_file = episode_path(scripts_root, season, episode)
        if not ep_file.exists():
            raise FileNotFoundError(f"Missing episode file: {ep_file}")

        lines = read_episode_lines(ep_file)

        if line_idx >= len(lines):
            season, episode = bump_episode(season, episode)
            state.update({"season": season, "episode": episode, "line": 0})
            save_state(state_path, state)
            continue

        line = lines[line_idx]
        text = f"S{season}E{episode} {line}"

        post(api, text, dry_run=dry_run)

        state["line"] = line_idx + 1
        save_state(state_path, state)

        if mode == "once":
            return

        time.sleep(interval)

if __name__ == "__main__":
    import sys
    mode = "continue"
    if len(sys.argv) > 1:
        mode = sys.argv[1].strip().lower()
    if mode not in {"continue", "once"}:
        raise SystemExit("Usage: python bot.py [continue|once]")
    run(mode)
