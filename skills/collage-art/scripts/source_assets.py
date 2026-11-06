#!/usr/bin/env python3
"""
source_assets.py — autonomous image sourcing for the collage pipeline.

Given a concept JSON (the output of the theme-extraction step), search
Wikimedia Commons for each visual motif, download licensed thumbnails and
write an attribution manifest. Only CC / public-domain results are kept.

Usage
-----
    python3 source_assets.py --concept concept.json --out-dir assets/session-01
    python3 source_assets.py --concept concept.json --out-dir assets/session-01 --offline

`--offline` is for tests and air-gapped runs: it creates no files, but still
reports the queries that would be issued, so the same concept file can be
validated before any network call.

Concept format (see references/concept-schema.md):

    {
      "theme": "...", "statement": "...",
      "motifs": [
        {"id": "moon", "query": "moon crater", "role": "hero", "why": "..."},
        {"id": "sea",  "query": "ocean wave", "role": "ground"}
      ]
    }

Requires: Python stdlib only for search; Pillow for the optional cutout helper.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = "ewen-collage/0.1 (collage-art skill; local research use)"
# Licences we are comfortable reusing. ShareAlike results are allowed but are
# recorded explicitly in the manifest so the final work can carry the same terms.
OK_LICENSES = {
    "public domain", "pd", "cc0", "cc by", "cc by-sa",
    "cc by 2.0", "cc by 3.0", "cc by 4.0",
    "cc by-sa 2.0", "cc by-sa 3.0", "cc by-sa 4.0",
    "attribution", "attribution-sharealike",
}


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s or "")).strip()


def license_ok(name):
    n = (name or "").lower().strip()
    if not n:
        return False
    return any(k in n for k in OK_LICENSES) and "all rights reserved" not in n


def search_commons(query, limit=6, timeout=20):
    """Return a list of candidate dicts with url, title, author, licence, page."""
    params = {
        "action": "query", "generator": "search",
        "gsrsearch": "filetype:bitmap " + query,
        "gsrnamespace": "6", "gsrlimit": str(limit),
        "prop": "imageinfo", "iiprop": "url|extmetadata|size",
        "iiurlwidth": "1600", "format": "json", "formatversion": "2",
    }
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        data = json.load(fh)
    out = []
    for page in data.get("query", {}).get("pages", []):
        ii = (page.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {}) or {}
        lic = strip_tags(meta.get("LicenseShortName", {}).get("value", ""))
        if not license_ok(lic):
            continue
        dl = ii.get("thumburl") or ii.get("url")
        if not dl:
            continue
        out.append({
            "query": query,
            "title": page.get("title", ""),
            "url": dl,
            "width": ii.get("thumbwidth") or ii.get("width"),
            "height": ii.get("thumbheight") or ii.get("height"),
            "license": lic,
            "license_url": strip_tags(meta.get("LicenseUrl", {}).get("value", "")),
            "artist": strip_tags(meta.get("Artist", {}).get("value", ""))[:200],
            "page": ii.get("descriptionurl", ""),
            "restrictions": strip_tags(meta.get("Restrictions", {}).get("value", "")),
        })
    return out


def download(url, path, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as fh:
        blob = fh.read()
    if len(blob) < 2000:
        raise ValueError("suspiciously small download (%d bytes)" % len(blob))
    with open(path, "wb") as f:
        f.write(blob)
    return len(blob)


def main():
    ap = argparse.ArgumentParser(description="Find and download licensed collage source imagery.")
    ap.add_argument("--concept", help="concept JSON with a motifs[] list")
    ap.add_argument("--out-dir", help="where to put downloaded jpgs + manifest")
    ap.add_argument("--per-motif", type=int, default=2, help="images per motif (default 2)")
    ap.add_argument("--offline", action="store_true", help="validate only; no network")
    ap.add_argument("--query-only", help="search a single ad-hoc query and print results as JSON")
    args = ap.parse_args()

    if args.query_only:
        print(json.dumps(search_commons(args.query_only, limit=6), ensure_ascii=False, indent=2))
        return
    if not args.concept or not args.out_dir:
        ap.error("--concept and --out-dir are required unless --query-only is used")

    with open(args.concept, encoding="utf-8") as f:
        concept = json.load(f)
    motifs = concept.get("motifs", [])
    if not motifs:
        sys.exit("concept has no motifs[] — run the theme-extraction step first")
    for i, m in enumerate(motifs):
        for key in ("id", "query"):
            if not m.get(key):
                sys.exit("motif #%d missing %r" % (i, key))

    if args.offline:
        print("offline: would query %d motifs" % len(motifs))
        for m in motifs:
            print("  %-14s <- %s" % (m["id"], m["query"]))
        return

    os.makedirs(args.out_dir, exist_ok=True)
    manifest = {
        "theme": concept.get("theme", ""),
        "statement": concept.get("statement", ""),
        "source": "Wikimedia Commons",
        "note": "Each entry keeps its own licence. CC BY / BY-SA works require attribution; "
                "BY-SA may also require the combined work to be shared alike.",
        "assets": [],
    }
    for m in motifs:
        try:
            candidates = search_commons(m["query"], limit=max(6, args.per_motif * 3))
        except Exception as e:
            print("search failed for %r: %s" % (m["query"], e), file=sys.stderr)
            continue
        used = 0
        for c in candidates:
            if c.get("restrictions") and "personality" in c["restrictions"].lower():
                continue  # avoid identifiable-person rights warnings
            if used >= args.per_motif:
                break
            safe = re.sub(r"[^a-z0-9_-]+", "-", m["id"].lower()).strip("-") or "motif"
            fn = "%s-%02d.jpg" % (safe, used + 1)
            path = os.path.join(args.out_dir, fn)
            try:
                size = download(c["url"], path)
            except Exception as e:
                print("download failed %s: %s" % (c["url"][:70], e), file=sys.stderr)
                continue
            manifest["assets"].append({
                "id": "%s-%02d" % (m["id"], used + 1),
                "motif": m["id"], "query": m["query"], "role": m.get("role", "satellite"),
                "why": m.get("why", ""), "file": fn, "bytes": size,
                "title": c["title"], "artist": c["artist"], "license": c["license"],
                "license_url": c["license_url"], "page": c["page"], "origin_url": c["url"],
            })
            used += 1
            time.sleep(0.25)  # be polite to the Commons API
        print("%-14s %d/%d image(s)" % (m["id"], used, args.per_motif))

    mpath = os.path.join(args.out_dir, "SOURCES.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("wrote %s (%d assets)" % (mpath, len(manifest["assets"])))
    if not manifest["assets"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
