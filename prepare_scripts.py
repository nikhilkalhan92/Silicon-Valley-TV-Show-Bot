import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv

SEASON_DIR_RE = re.compile(r"^SEASON\s+(\d+)$", re.IGNORECASE)
EP_NUM_RE = re.compile(r"Episode\s+(\d+)", re.IGNORECASE)

def parse_screenplay(text: str):
    """
    Silicon Valley dataset contains dialogue only (no speaker names).
    We treat each meaningful non-empty line as tweetable dialogue.
    """
    lines = []

    for ln in text.splitlines():
        s = ln.strip()

        # Skip empty lines
        if not s:
            continue

        # Skip obvious non-dialogue metadata
        if s.isupper() and len(s) > 30:
            continue
        if s.startswith(("INT.", "EXT.")):
            continue
        if s.lower().startswith(("written by", "directed by", "produced by")):
            continue

        lines.append(s)

    return lines


def main():
    load_dotenv()

    raw_root = os.getenv("RAW_ROOT")
    scripts_root = Path(os.getenv("SCRIPTS_ROOT", "./scripts")).resolve()

    if not raw_root:
        raise SystemExit("ERROR: RAW_ROOT not set in .env")

    raw_root = Path(raw_root).resolve()
    scripts_root.mkdir(parents=True, exist_ok=True)

    season_dirs = []
    for p in raw_root.iterdir():
        m = SEASON_DIR_RE.match(p.name)
        if p.is_dir() and m:
            season_dirs.append(p)

    season_dirs.sort(key=lambda p: int(SEASON_DIR_RE.match(p.name).group(1)))

    if not season_dirs:
        raise SystemExit(f"ERROR: No season folders found under {raw_root}")

    manifest = []
    total_eps = 0
    total_lines = 0

    for season_dir in season_dirs:
        season_num = int(SEASON_DIR_RE.match(season_dir.name).group(1))

        for ep_file in sorted(season_dir.glob("*.txt")):
            m = EP_NUM_RE.search(ep_file.name)
            if not m:
                print(f"Skipping (no episode number): {ep_file.name}")
                continue

            ep_num = int(m.group(1))

            text = ep_file.read_text(encoding="utf-8", errors="ignore")
            lines = parse_screenplay(text)

            out_dir = scripts_root / str(season_num) / str(ep_num)
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"{ep_num}.txt"
            out_path.write_text("\n".join(lines), encoding="utf-8")

            print(f"Wrote S{season_num}E{ep_num}: {len(lines)} lines")

            manifest.append({
                "season": season_num,
                "episode": ep_num,
                "source": str(ep_file),
                "out": str(out_path),
                "lines": len(lines),
            })

            total_eps += 1
            total_lines += len(lines)

    (scripts_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8"
    )

    print(f"\nDone.")
    print(f"Episodes processed: {total_eps}")
    print(f"Total dialogue lines: {total_lines}")
    print(f"Scripts output: {scripts_root}")


if __name__ == "__main__":
    main()
