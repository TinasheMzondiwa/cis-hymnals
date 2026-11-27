#!/usr/bin/env python3
"""
CI validator for hymnal data files in cis-hymnals repository.
Validates JSON syntax, schema compliance, data cleanliness (no raw HTML, no \\ufffd),
v2/config.json consistency, and preview/app.js configuration synchronization.
"""

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

HTML_TAG_RE = re.compile(r'<\/?(?:br|p|i|b|font|span|div|h[1-6]|em|strong)[^>]*>', re.IGNORECASE)
REPLACEMENT_CHAR_RE = re.compile(r'[\ufffd\x00]')

class ValidationResult:
    def __init__(self, use_github_annotations=False):
        self.errors = []
        self.warnings = []
        self.use_github_annotations = use_github_annotations

    def add_error(self, message, file_path=None, line=None):
        self.errors.append((message, file_path, line))
        if self.use_github_annotations and file_path:
            loc = f"file={file_path}"
            if line:
                loc += f",line={line}"
            print(f"::error {loc}::{message}")
        else:
            prefix = f"[{file_path}] " if file_path else ""
            print(f"ERROR: {prefix}{message}")

    def add_warning(self, message, file_path=None, line=None):
        self.warnings.append((message, file_path, line))
        if self.use_github_annotations and file_path:
            loc = f"file={file_path}"
            if line:
                loc += f",line={line}"
            print(f"::warning {loc}::{message}")
        else:
            prefix = f"[{file_path}] " if file_path else ""
            print(f"WARNING: {prefix}{message}")

    @property
    def has_errors(self):
        return len(self.errors) > 0


def validate_config(config_path, repo_root, result):
    """Validates v2/config.json structure and matches with existing files."""
    if not config_path.exists():
        result.add_error("Configuration file missing", str(config_path))
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        result.add_error(f"Failed to parse JSON: {e}", str(config_path))
        return None

    if not isinstance(config, list) or len(config) == 0:
        result.add_error("Root must be a non-empty list of language objects", str(config_path))
        return None

    seen_keys = set()
    v2_dir = repo_root / "v2"

    for idx, item in enumerate(config):
        if not isinstance(item, dict):
            result.add_error(f"Item #{idx} is not an object", str(config_path))
            continue

        key = item.get("key")
        title = item.get("title")
        language = item.get("language")

        if not key or not isinstance(key, str):
            result.add_error(f"Item #{idx} missing valid 'key'", str(config_path))
            continue

        if key in seen_keys:
            result.add_error(f"Duplicate key '{key}' found in config", str(config_path))
        seen_keys.add(key)

        if not title or not isinstance(title, str):
            result.add_error(f"Item '{key}' missing valid 'title'", str(config_path))
        if not language or not isinstance(language, str):
            result.add_error(f"Item '{key}' missing valid 'language'", str(config_path))

        # Check that at least one matching hymnal file exists in v2/
        matching = list(v2_dir.glob(f"{key}/*.json")) + list(v2_dir.glob(f"*/{key}.json"))
        # Special alias checks if key is short (e.g. ru, pt, es, dg, sdah)
        if not matching:
            for p in v2_dir.glob("*/*.json"):
                if p.stem.lower() == key.lower():
                    matching.append(p)
                    break
        if not matching:
            result.add_error(f"Config key '{key}' has no corresponding hymnal JSON file in v2/", str(config_path))

    return config


def validate_preview_sync(preview_app_path, config_data, result):
    """Checks that EMBEDDED_CONFIG in preview/app.js is in sync with v2/config.json."""
    if not preview_app_path.exists() or not config_data:
        return

    try:
        content = preview_app_path.read_text(encoding="utf-8")
        match = re.search(r"const\s+EMBEDDED_CONFIG\s*=\s*(\[[\s\S]*?\]);", content)
        if not match:
            result.add_warning("Could not extract EMBEDDED_CONFIG from preview/app.js", str(preview_app_path))
            return

        embedded_config = json.loads(match.group(1))
        config_keys = [c.get("key") for c in config_data]
        embedded_keys = [c.get("key") for c in embedded_config]

        if config_keys != embedded_keys:
            result.add_warning(
                f"EMBEDDED_CONFIG in preview/app.js is out of sync with v2/config.json "
                f"(diff: {set(config_keys) ^ set(embedded_keys)})",
                str(preview_app_path)
            )
    except Exception as e:
        result.add_warning(f"Error checking preview/app.js sync: {e}", str(preview_app_path))


def validate_hymnal_file(file_path, result):
    """Validates a single hymnal JSON file."""
    rel_path = str(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            hymns = json.load(f)
    except UnicodeDecodeError as e:
        result.add_error(f"Encoding error (file must be UTF-8): {e}", rel_path)
        return
    except Exception as e:
        result.add_error(f"Invalid JSON: {e}", rel_path)
        return

    if not isinstance(hymns, list) or len(hymns) == 0:
        result.add_error("Root must be a non-empty list of hymn objects", rel_path)
        return

    numbers_seen = set()

    for idx, hymn in enumerate(hymns):
        if not isinstance(hymn, dict):
            result.add_error(f"Hymn at index {idx} is not an object", rel_path)
            continue

        number = hymn.get("number")
        if number is None or not isinstance(number, int) or number <= 0:
            result.add_error(f"Hymn at index {idx} must have a positive integer 'number'", rel_path)
        elif number in numbers_seen:
            result.add_error(f"Duplicate hymn number {number}", rel_path)
        else:
            numbers_seen.add(number)

        hymn_id = f"Hymn #{number}" if number is not None else f"Hymn at index {idx}"

        # Title check
        title = hymn.get("title")
        if not isinstance(title, str) or not title.strip():
            result.add_warning(f"{hymn_id} has empty title", rel_path)
        elif HTML_TAG_RE.search(title):
            result.add_error(f"{hymn_id} title contains unstripped HTML: {title}", rel_path)
        elif REPLACEMENT_CHAR_RE.search(title):
            result.add_error(f"{hymn_id} title contains invalid character (\\ufffd or null)", rel_path)

        # Revision check (optional for legacy files unless strict)
        revision = hymn.get("revision")
        if revision is not None and (not isinstance(revision, int) or revision < 1):
            result.add_error(f"{hymn_id} has invalid 'revision' ({revision}); expected int >= 1", rel_path)

        # Lyrics check
        lyrics = hymn.get("lyrics")
        if not isinstance(lyrics, list) or len(lyrics) == 0:
            result.add_error(f"{hymn_id} has missing or empty 'lyrics' array", rel_path)
            continue

        for s_idx, stanza in enumerate(lyrics):
            stanza_id = f"{hymn_id}, stanza {s_idx + 1}"
            if not isinstance(stanza, dict):
                result.add_error(f"{stanza_id} is not an object", rel_path)
                continue

            stype = stanza.get("type")
            if stype not in ("verse", "refrain"):
                result.add_error(f"{stanza_id} has invalid type '{stype}' (expected 'verse' or 'refrain')", rel_path)

            lines = stanza.get("lines")
            if not isinstance(lines, list) or len(lines) == 0:
                result.add_error(f"{stanza_id} must have a non-empty 'lines' list", rel_path)
                continue

            for l_idx, line in enumerate(lines):
                line_id = f"{stanza_id}, line {l_idx + 1}"
                if not isinstance(line, str):
                    result.add_error(f"{line_id} is not a string", rel_path)
                    continue

                if not line.strip():
                    result.add_error(f"{line_id} is empty or whitespace-only", rel_path)

                if HTML_TAG_RE.search(line):
                    result.add_error(f"{line_id} contains raw HTML tag: '{line[:40]}...'", rel_path)

                if REPLACEMENT_CHAR_RE.search(line):
                    result.add_error(f"{line_id} contains replacement character (\\ufffd)", rel_path)


def get_changed_files(repo_root, base_ref="origin/main"):
    """Returns list of changed files compared to base ref."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL
        ).decode("utf-8")
        files = [repo_root / line.strip() for line in out.splitlines() if line.strip()]
        return [f for f in files if f.exists()]
    except Exception:
        return []


def main():
    parser = argparse.ArgumentParser(description="Validate cis-hymnals v2 data files.")
    parser.add_argument("files", nargs="*", help="Specific JSON files to validate.")
    parser.add_argument("--all", action="store_true", help="Validate all hymnal files under v2/.")
    parser.add_argument("--changed-only", action="store_true", help="Validate only files changed in this branch vs main.")
    parser.add_argument("--github-actions", action="store_true", help="Emit GitHub Actions annotation commands.")
    parser.add_argument("--base-ref", default="origin/main", help="Git base ref for --changed-only (default: origin/main).")
    args = parser.parse_args()

    repo_root = pathlib.Path(__file__).resolve().parent.parent
    result = ValidationResult(use_github_annotations=args.github_actions)

    v2_config_path = repo_root / "v2" / "config.json"
    preview_app_path = repo_root / "preview" / "app.js"

    # Always validate v2/config.json and preview/app.js sync
    print("Validating v2/config.json and preview/app.js...")
    config_data = validate_config(v2_config_path, repo_root, result)
    validate_preview_sync(preview_app_path, config_data, result)

    target_files = []
    if args.files:
        for f in args.files:
            p = pathlib.Path(f).resolve()
            if p.exists() and p.suffix == ".json":
                target_files.append(p)
    elif args.changed_only:
        changed = get_changed_files(repo_root, base_ref=args.base_ref)
        target_files = [f for f in changed if f.suffix == ".json" and "v2" in f.parts and f.name != "config.json"]
        print(f"Discovered {len(target_files)} changed hymnal file(s) against {args.base_ref}")
    else:
        # Default or --all
        target_files = sorted((repo_root / "v2").glob("*/*.json"))
        print(f"Validating all {len(target_files)} hymnal files under v2/...")

    for file_path in target_files:
        rel = file_path.relative_to(repo_root) if repo_root in file_path.parents else file_path
        print(f"Checking {rel}...")
        validate_hymnal_file(file_path, result)

    print("\n" + "=" * 50)
    print(f"Validation summary: {len(result.errors)} error(s), {len(result.warnings)} warning(s).")
    print("=" * 50)

    if result.has_errors:
        sys.exit(1)
    else:
        print("All checks passed successfully! ✨")
        sys.exit(0)


if __name__ == "__main__":
    main()
