#!/usr/bin/env python3
"""
Standalone test utility to fetch the same monster tokens you see on 5e.tools.

It tries:
- The community GitHub mirror
- The official 5e.tools image hosting (with both underscore and %20 versions)

Usage:
    uv run python utilities/test_monster_images.py --name "Ancient Red Dragon" --verbose
"""

import argparse
import json
import re
import urllib.parse
from pathlib import Path
from typing import Any, List, Tuple

import requests

MIRROR_BASE = "https://raw.githubusercontent.com/5etools-mirror-3/5etools-img/main/img/bestiary/tokens"
OFFICIAL_BASE = "https://5e.tools/img/bestiary/tokens"


def sanitize_name(name: str) -> str:
    name = re.sub(r"[^\w\s-]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    return name


def load_monster(name: str | None = None, monster_id: str | None = None) -> dict[str, Any] | None:
    bestiary_path = Path("data/srd/monsters.json")
    if not bestiary_path.exists():
        print(f"[ERROR] Bestiary not found: {bestiary_path}")
        return None

    with open(bestiary_path, encoding="utf-8") as f:
        data = json.load(f)

    for m in data:
        if monster_id and m.get("id") == monster_id:
            return m
        if name and m.get("name", "").lower() == name.lower():
            return m
    return None


def build_candidate_urls(monster: dict[str, Any]) -> List[Tuple[str, str]]:
    """Generate likely token URLs, including the version 5e.tools actually uses in the browser."""
    urls: List[Tuple[str, str]] = []
    name = monster.get("name", "")
    source = monster.get("source", "") or ""
    sanitized = sanitize_name(name)                    # Ancient_Red_Dragon
    encoded = urllib.parse.quote(name)                 # Ancient%20Red%20Dragon
    stored_path = monster.get("image_path")

    # GitHub mirror (usually only has the underscore version)
    if source:
        urls.append(("mirror", f"{MIRROR_BASE}/{source}/{sanitized}.webp"))
        urls.append(("mirror", f"{MIRROR_BASE}/{source}/{sanitized}.png"))
    urls.append(("mirror", f"{MIRROR_BASE}/{sanitized}.webp"))
    urls.append(("mirror", f"{MIRROR_BASE}/{sanitized}.png"))

    # Official 5e.tools site — try both naming styles
    name_variants = [sanitized, encoded]
    for variant in name_variants:
        if source:
            urls.append(("official", f"{OFFICIAL_BASE}/{source}/{variant}.webp"))
            urls.append(("official", f"{OFFICIAL_BASE}/{source}/{variant}.png"))
        urls.append(("official", f"{OFFICIAL_BASE}/{variant}.webp"))
        urls.append(("official", f"{OFFICIAL_BASE}/{variant}.png"))

    # Try the stored image_path as a last resort
    if stored_path:
        filename = Path(stored_path).name
        urls.append(("mirror", f"{MIRROR_BASE}/{filename}"))
        urls.append(("official", f"{OFFICIAL_BASE}/{filename}"))

    # Deduplicate
    seen = set()
    final = []
    for label, url in urls:
        if url not in seen:
            seen.add(url)
            final.append((label, url))
    return final


def get_local_save_path(monster: dict[str, Any], ext: str = ".webp") -> Path:
    name = monster.get("name", "")
    source = monster.get("source", "") or ""
    sanitized = sanitize_name(name)
    base = Path("data/images/bestiary/tokens")
    if source:
        base = base / source
    return base / f"{sanitized}{ext}"


def try_download(url: str, dest: Path, label: str, verbose: bool) -> bool:
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        status = resp.status_code
        size = len(resp.content)

        if verbose:
            print(f"  [{label}] [{status}] {url} ({size} bytes)")

        if status == 200 and size > 1000:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.content)
            return True
    except Exception as e:
        if verbose:
            print(f"  [{label}] [ERR] {url} -> {e}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="Monster name (e.g. 'Ancient Red Dragon')")
    parser.add_argument("--id", help="Monster ID")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    if not args.name and not args.id:
        parser.error("Please provide --name or --id")

    monster = load_monster(name=args.name, monster_id=args.id)
    if not monster:
        print("Monster not found")
        return

    print(f"Monster: {monster['name']} (source: {monster.get('source', 'N/A')})")
    print(f"has_token: {monster.get('has_token')}, image_path: {monster.get('image_path')}\n")

    # Probe for existing local file under either common extension first (fast path for re-runs)
    for probe_ext in (".webp", ".png"):
        p = get_local_save_path(monster, probe_ext)
        if p.exists() and p.stat().st_size > 500:
            print(f"[OK] Already have it locally: {p}")
            return

    print("Attempting download...\n")

    candidates = build_candidate_urls(monster)
    print(f"Will try {len(candidates)} URLs (mirror + official 5e.tools)\n")

    success = False
    saved_path = None
    for label, url in candidates:
        # Compute dest path with correct ext for this particular URL
        ext = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".png"
        if ext not in (".png", ".webp", ".jpg", ".jpeg"):
            ext = ".png"
        dest = get_local_save_path(monster, ext)
        if dest.exists() and dest.stat().st_size > 500:
            print(f"[OK] Already have it locally: {dest}")
            return
        if try_download(url, dest, label, verbose=True):
            print(f"\n[SUCCESS] Saved to: {dest}")
            success = True
            saved_path = dest
            break

    if not success:
        # Fallback suggestion uses .webp (most common for tokens that exist)
        fallback = get_local_save_path(monster, ".webp")
        print("\n[FAILED] Still couldn't get the image.")
        print(f"Best place to save it manually: {fallback}")
        print("\nTip: On 5e.tools, right-click the token image → 'Save image as...' and put it at the path above.")


if __name__ == "__main__":
    main()
