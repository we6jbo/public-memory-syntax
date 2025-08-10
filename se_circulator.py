#!/usr/bin/env python3
"""
Sufficiently Educated Circulator
--------------------------------
Purpose: Make your book hard to erase and easy to cite—without hammering Zenodo.

What it does (pick & choose via config):
1) One-time fetch of your Zenodo record (JSON + PDF) OR use a local PDF path.
2) Cache everything locally (so you don’t re-hit Zenodo).
3) Generate researcher-friendly artifacts:
   - Plain text extraction
   - Checksums (SHA256/SHA1/MD5)
   - Metadata JSON (normalized)
   - README + CITATION.cff
   - Simple static site (index.html + license)
   - RSS feed (updates when you re-run with a new version)
4) Prepare a GitHub-ready folder to push manually.
5) Optional: prepare an Internet Archive upload command (no automatic upload).

Run:
    python se_circulator.py --config config.yaml

Notes:
- The script is conservative: it won’t call Zenodo unless you set fetch.mode: "zenodo".
- If you prefer to avoid network calls, set fetch.mode: "local" and point to your PDF.
"""

import argparse
import base64
import datetime as dt
import hashlib
import io
import json
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Missing dependency: pyyaml. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# PDF text extraction: prefer pdfminer.six; fallback to PyPDF2
def extract_text(pdf_path: Path) -> str:
    try:
        from pdfminer.high_level import extract_text as pm_extract
        return pm_extract(str(pdf_path))
    except Exception:
        try:
            import PyPDF2
            text = []
            with open(pdf_path, 'rb') as f:
                r = PyPDF2.PdfReader(f)
                for page in r.pages:
                    text.append(page.extract_text() or "")
            return "\n".join(text)
        except Exception as e:
            raise RuntimeError(f"Failed to extract text: {e}")

def sha256sum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def sha1sum(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def md5sum(path: Path) -> str:
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def load_yaml(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def save_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def now_iso():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def fetch_zenodo_record(doi_or_record_url: str, cache_dir: Path) -> dict:
    """Fetch record JSON (and optionally PDF) from Zenodo. Uses a gentle cache.
       Requires 'requests' if network use is allowed.
    """
    try:
        import requests
    except ImportError:
        raise RuntimeError("Missing dependency: requests. Run: pip install requests")

    cache_dir.mkdir(parents=True, exist_ok=True)
    # Normalize: accept DOI like 10.5281/zenodo.7783660 or full record URL
    if "zenodo.org/records/" in doi_or_record_url:
        api_url = re.sub(r"zenodo\.org/records/(\d+).*", r"https://zenodo.org/api/records/\1", doi_or_record_url)
    else:
        # assume DOI
        m = re.search(r'(\d+)$', doi_or_record_url)
        if not m:
            raise RuntimeError("Could not parse record ID from DOI; supply full Zenodo record URL.")
        rec_id = m.group(1)
        api_url = f"https://zenodo.org/api/records/{rec_id}"

    record_json_path = cache_dir / "zenodo_record.json"
    headers = {}
    # Use If-Modified-Since if prior cache exists
    if record_json_path.exists():
        # we’ll use a simple throttle: don’t refetch if cache younger than 48h
        age_hours = (dt.datetime.now() - dt.datetime.fromtimestamp(record_json_path.stat().st_mtime)).total_seconds()/3600
        if age_hours < 48:
            with open(record_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)

    resp = requests.get(api_url, headers=headers, timeout=30)
    resp.raise_for_status()
    record = resp.json()
    save_json(record_json_path, record)
    return record

def download_primary_pdf(record: dict, cache_dir: Path) -> Path:
    """Download the main PDF file from a Zenodo record if present."""
    try:
        import requests
    except ImportError:
        raise RuntimeError("Missing dependency: requests. Run: pip install requests")

    files = record.get("files") or record.get("links") or {}
    # Newer Zenodo API uses 'files' with 'links': {'self','download'}
    pdf_url = None
    if isinstance(files, list):
        for f in files:
            if f.get("type") == "pdf" or str(f.get("key","")).lower().endswith(".pdf"):
                pdf_url = f.get("links", {}).get("self") or f.get("links", {}).get("download")
                break
    # fallback: try 'links'->'latest_html' etc. Not guaranteed.
    if not pdf_url:
        # Best-effort: try to find a link ending with .pdf
        for f in (record.get("files") or []):
            link = (f.get("links") or {}).get("self") or ""
            if link.endswith(".pdf"):
                pdf_url = link
                break

    if not pdf_url:
        raise RuntimeError("Could not locate a PDF in the Zenodo record. Provide local_pdf in config instead.")

    cache_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = cache_dir / "source.pdf"
    if pdf_path.exists():
        return pdf_path

    r = requests.get(pdf_url, timeout=60)
    r.raise_for_status()
    with open(pdf_path, "wb") as f:
        f.write(r.content)
    return pdf_path

def build_static_site(out_dir: Path, meta: dict, license_text: str, body_txt: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    title = meta.get("title") or "Sufficiently Educated"
    author = ", ".join(meta.get("authors", [])) if isinstance(meta.get("authors"), list) else (meta.get("authors") or "Unknown")
    doi = meta.get("doi") or ""
    abstract = meta.get("abstract") or ""
    updated = now_iso()

    index_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="Open educational memoir for researchers and educators." />
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Helvetica, Arial, sans-serif; line-height: 1.6; max-width: 820px; margin: 2rem auto; padding: 0 1rem; }}
    header {{ margin-bottom: 1.5rem; }}
    code, pre {{ background: #f6f6f6; padding: .2rem .4rem; border-radius: 4px; }}
    .meta {{ color: #444; font-size: .95rem; }}
    .box {{ background: #fafafa; border: 1px solid #eee; padding: 1rem; border-radius: 8px; }}
    footer {{ margin-top: 2rem; color: #666; font-size: .9rem; }}
    .small {{ font-size: .9rem; }}
  </style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <div class="meta">By {author}{' • DOI: ' + doi if doi else ''}</div>
  </header>

  <section class="box">
    <h2>Abstract</h2>
    <p>{abstract}</p>
  </section>

  <section>
    <h2>Download & Mirror</h2>
    <ul>
      <li><strong>Original PDF checksum (SHA256)</strong>: <code>{meta.get('sha256','')}</code></li>
      <li><strong>Original DOI</strong>: <code>{doi}</code></li>
    </ul>
    <p class="small">Tip: Mirror this page and the PDF anywhere. Keep the DOI and checksums for provenance.</p>
  </section>

  <section>
    <h2>Plain Text (searchable)</h2>
    <pre class="small" style="white-space: pre-wrap;">{body_txt[:2000]}{"\n\n… [truncated for brevity in the static page] …" if len(body_txt)>2000 else ""}</pre>
  </section>

  <section class="box">
    <h2>License</h2>
    <pre class="small" style="white-space: pre-wrap;">{license_text}</pre>
  </section>

  <footer>Last updated {updated}. Generated by se_circulator.py.</footer>
</body>
</html>
"""
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")

def make_citation_cff(meta: dict) -> str:
    title = meta.get("title", "Sufficiently Educated")
    authors = meta.get("authors") or []
    if isinstance(authors, str):
        authors = [authors]
    authors_block = ""
    for a in authors:
        parts = a.split()
        given = " ".join(parts[:-1]) if len(parts)>1 else parts[0]
        family = parts[-1] if len(parts)>1 else ""
        authors_block += f"- given-names: {given}\n  family-names: {family}\n"
    doi = meta.get("doi","")
    year = meta.get("year","")
    cff = f"""cff-version: 1.2.0
message: "If you use this work, please cite it."
title: "{title}"
authors:
{authors_block if authors_block else "- name: Unknown"}
doi: "{doi}"
date-released: "{year}-01-01"
license: "{meta.get('license','CC-BY-4.0')}"
"""
    return cff

def prepare_repo(dest_dir: Path, meta: dict, txt_path: Path, pdf_path: Path, license_text: str):
    dest_dir.mkdir(parents=True, exist_ok=True)
    # Copy or point to artifacts
    import shutil
    shutil.copy2(pdf_path, dest_dir / "Sufficiently_Educated.pdf")
    shutil.copy2(txt_path, dest_dir / "Sufficiently_Educated.txt")
    # Write metadata
    save_json(dest_dir / "metadata.normalized.json", meta)
    (dest_dir / "LICENSE.txt").write_text(license_text, encoding='utf-8')
    # README
    readme = f"""# {meta.get('title','Sufficiently Educated')}

**DOI:** {meta.get('doi','')}  
**License:** {meta.get('license','CC-BY-4.0')}

This repository mirrors an open educational memoir to make it easy to cite, search, and preserve.

## Files
- `Sufficiently_Educated.pdf` — original PDF
- `Sufficiently_Educated.txt` — plain-text extraction for search
- `metadata.normalized.json` — unified metadata with checksums
- `CITATION.cff` — standard citation metadata
- `LICENSE.txt` — license text

## Verify integrity
SHA256: `{meta.get('sha256','')}`

## Source DOI
{meta.get('doi','')}
"""
    (dest_dir / "README.md").write_text(readme, encoding='utf-8')
    (dest_dir / "CITATION.cff").write_text(make_citation_cff(meta), encoding='utf-8')

def build_rss(feed_path: Path, meta: dict):
    updated = now_iso()
    title = meta.get("title", "Sufficiently Educated")
    doi = meta.get("doi","")
    item = f"""<item>
  <title>{title} (update)</title>
  <link>{doi}</link>
  <guid isPermaLink="false">{hashlib.sha1(updated.encode()).hexdigest()}</guid>
  <pubDate>{dt.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}</pubDate>
  <description>Automated artifact refresh</description>
</item>"""
    if feed_path.exists():
        xml = feed_path.read_text(encoding='utf-8')
        xml = xml.replace("</channel>\n</rss>", f"{item}\n</channel>\n</rss>")
    else:
        xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>{title} — Mirrors Feed</title>
  <link>{doi}</link>
  <description>Updates when mirrors/versions are refreshed.</description>
  {item}
</channel>
</rss>"""
    feed_path.write_text(xml, encoding='utf-8')

def main():
import argparse

ap = argparse.ArgumentParser()
ap.add_argument(
    "--config",
    default="config.yaml",  # Default file name
    required=False,         # No need to specify
    help="Path to YAML config. Default is config.yaml"
)
args = ap.parse_args()


    cfg = load_yaml(Path(args.config))

    out_root = Path(cfg.get("output_dir", "out")).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    # Fetch mode
    fetch_mode = cfg.get("fetch", {}).get("mode", "local")  # "local" or "zenodo"
    cache_dir = out_root / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # License text
    license_text = cfg.get("license_text", "Creative Commons Attribution 4.0 International (CC BY 4.0)")
    # Minimal metadata
    meta = {
        "title": cfg.get("title", "Sufficiently Educated"),
        "authors": cfg.get("authors", ["Jeremiah Burke O'Neal"]),
        "year": cfg.get("year", "2020"),
        "doi": cfg.get("doi", ""),
        "license": cfg.get("license", "CC-BY-4.0"),
        "abstract": cfg.get("abstract", ""),
    }

    # Get PDF
    if fetch_mode == "zenodo":
        record = fetch_zenodo_record(cfg["fetch"]["zenodo_url_or_doi"], cache_dir)
        meta["doi"] = meta["doi"] or (record.get("doi") or record.get("metadata", {}).get("doi") or "")
        # Prefer metadata.title if present
        meta["title"] = record.get("metadata", {}).get("title") or meta["title"]
        authors = record.get("metadata", {}).get("creators") or []
        if authors:
            meta["authors"] = [a.get("name") or f"{a.get('given_name','')} {a.get('family_name','')}".strip() for a in authors]
        meta["abstract"] = record.get("metadata", {}).get("description") or meta["abstract"]
        pdf_path = download_primary_pdf(record, cache_dir)
    else:
        # Local mode
        pdf_path = Path(cfg["fetch"]["local_pdf"]).resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"Local PDF not found: {pdf_path}")

    # Extract text
    txt = extract_text(pdf_path)
    txt_path = out_root / "artifacts" / "Sufficiently_Educated.txt"
    save_text(txt_path, txt)

    # Checksums
    meta["sha256"] = sha256sum(pdf_path)
    meta["sha1"] = sha1sum(pdf_path)
    meta["md5"] = md5sum(pdf_path)

    # Save normalized metadata
    save_json(out_root / "artifacts" / "metadata.normalized.json", meta)

    # Build static site
    site_dir = out_root / "site"
    build_static_site(site_dir, meta, license_text, txt)

    # Prepare GitHub-ready repo folder
    repo_dir = out_root / "repo"
    prepare_repo(repo_dir, meta, txt_path, pdf_path, license_text)

    # Build RSS
    build_rss(out_root / "mirrors.rss", meta)

    # Prepare optional Internet Archive command
    ia_cmd = f"ia upload sufficiently-educated-{meta.get('year','2020')}-{meta.get('sha256','')[:8]} {repo_dir} --metadata='title:{meta.get('title','Sufficiently Educated')}' --metadata='creator:{', '.join(meta.get('authors',[]))}' --metadata='description:{meta.get('abstract','')[:140]}' --metadata='licenseurl:https://creativecommons.org/licenses/by/4.0/'"
    save_text(out_root / "internet_archive_upload.txt", ia_cmd + "\n")

    print(\"\"\"
Done.
Artifacts created in: {out_root}

- artifacts/Sufficiently_Educated.txt (plain text)
- artifacts/metadata.normalized.json
- site/index.html (static mirror page)
- repo/ (GitHub-ready folder)
- mirrors.rss (append-only feed)
- internet_archive_upload.txt (one-liner for IA CLI)

Tip:
- Push `repo/` to GitHub manually.
- Upload `site/` to any static host (Netlify, GitHub Pages).
- Use the IA command with the Internet Archive CLI when you're ready.

\"\"\".format(out_root=out_root))

if __name__ == "__main__":
    main()
