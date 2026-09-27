#!/usr/bin/env python
"""Checks every skill in the repo before it ships.

For each skills/<name>/SKILL.md:
  - frontmatter: `name` is lowercase-hyphenated, at most 64 chars and equal to the folder;
    `description` is present and at most 1024 chars
  - SKILL.md stays under 500 lines
  - `scripts/...`, `references/...` and `assets/...` paths quoted in backticks exist in the skill
  - when the skill ships scripts/pixelmap.py: every assets/*.txt map (and each of its declared
    variants) still renders and passes the script's checks, and every map is listed in the
    SKILL.md library table, with no table row pointing at a missing map

For every Markdown file in the repo: relative links and <img src> targets exist.

Usage:
    python scripts/validate.py

Exits 1 and lists every problem when anything fails. Requires Pillow for the map renders.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
DESCRIPTION_MAX = 1024
SKILL_MAX_LINES = 500
RENDER_ERROR_LINES = 8
FIELD_RE = re.compile(r"^([A-Za-z][\w-]*):\s*(.*)$")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)|\bsrc=\"([^\"]+)\"")
CODE_REF_RE = re.compile(r"`((?:scripts|references|assets)/[^`\s]+)`")
TABLE_MAP_RE = re.compile(r"^\|\s*`([\w-]+\.txt)`", re.M)
VARIANT_RE = re.compile(r"^\s*#\s*(?:variant|variante)\s+(\S+)\s*:", re.M)


def parse_frontmatter(text):
    """Returns the frontmatter as {key: value}, folding `>`/`|` block scalars into one line, or None."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields, key = {}, None
    for line in lines[1:]:
        if line.strip() == "---":
            return {k: " ".join(v).strip() for k, v in fields.items()}
        mt = FIELD_RE.match(line)
        if mt and not line[0].isspace():
            key, value = mt.group(1), mt.group(2).strip()
            fields[key] = [] if value in (">", ">-", "|", "|-") else [value]
        elif key and line.strip():
            fields[key].append(line.strip())
    return None


def check_skill_file(path):
    text = path.read_text(encoding="utf-8")
    fields = parse_frontmatter(text)
    if fields is None:
        return [f"{rel(path)}: missing or unterminated '---' frontmatter"]
    errors = []
    name, description = fields.get("name", ""), fields.get("description", "")
    folder = path.parent.name
    if not NAME_RE.match(name) or len(name) > NAME_MAX:
        errors.append(f"{rel(path)}: name '{name}' must be lowercase letters, digits and single hyphens, "
                      f"at most {NAME_MAX} chars")
    if name != folder:
        errors.append(f"{rel(path)}: name '{name}' must equal its folder '{folder}'")
    if not description:
        errors.append(f"{rel(path)}: description is missing")
    elif len(description) > DESCRIPTION_MAX:
        errors.append(f"{rel(path)}: description is {len(description)} chars (max {DESCRIPTION_MAX})")
    line_count = len(text.splitlines())
    if line_count > SKILL_MAX_LINES:
        errors.append(f"{rel(path)}: {line_count} lines (max {SKILL_MAX_LINES}); move detail to references/")
    return errors


def without_code_blocks(text):
    return re.sub(r"^```.*?^```", "", text, flags=re.M | re.S)


def check_links(md_path):
    errors = []
    for mt in LINK_RE.finditer(without_code_blocks(md_path.read_text(encoding="utf-8"))):
        target = (mt.group(1) or mt.group(2)).split("#")[0]
        if not target or re.match(r"^[a-z]+:", target):
            continue
        if not (md_path.parent / target).exists():
            errors.append(f"{rel(md_path)}: broken link '{target}'")
    return errors


def check_code_refs(skill_md):
    text = skill_md.read_text(encoding="utf-8")
    return [f"{rel(skill_md)}: `{ref}` does not exist in the skill"
            for ref in sorted(set(CODE_REF_RE.findall(text))) if not (skill_md.parent / ref).exists()]


def check_map_library(skill_md):
    listed = set(TABLE_MAP_RE.findall(skill_md.read_text(encoding="utf-8")))
    maps = {p.name for p in (skill_md.parent / "assets").glob("*.txt")}
    return ([f"{rel(skill_md)}: assets/{m} is missing from the library table" for m in sorted(maps - listed)]
            + [f"{rel(skill_md)}: library table lists {m}, which is not in assets/" for m in sorted(listed - maps)])


def map_variants(map_path):
    return [v.lower() for v in VARIANT_RE.findall(map_path.read_text(encoding="utf-8-sig"))]


def check_map_renders(skill_dir):
    """Renders every map the way SKILL.md tells the agent to, so a script or map change that breaks one fails here."""
    pixelmap = skill_dir / "scripts" / "pixelmap.py"
    errors = []
    with tempfile.TemporaryDirectory() as out_dir:
        for map_path in sorted((skill_dir / "assets").glob("*.txt")):
            for variant in [""] + map_variants(map_path):
                cmd = [sys.executable, str(pixelmap), "render", "--map", str(map_path),
                       "--out", str(Path(out_dir) / "map.png"), "--auto-outline"]
                if variant:
                    cmd += ["--variant", variant]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    label = rel(map_path) + (f" (variant {variant})" if variant else "")
                    detail = result.stderr.strip().splitlines()
                    if len(detail) > RENDER_ERROR_LINES:
                        detail = detail[:RENDER_ERROR_LINES] + [f"... ({len(detail) - RENDER_ERROR_LINES} more lines)"]
                    errors.append(f"{label}: render failed\n    " + "\n    ".join(detail))
    return errors


def markdown_files():
    return [p for p in ROOT.rglob("*.md") if not SKIP_DIRS & set(p.relative_to(ROOT).parts)]


def rel(path):
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main():
    skill_files = sorted(ROOT.glob("skills/*/SKILL.md"))
    errors = []
    for skill_md in skill_files:
        errors += check_skill_file(skill_md) + check_code_refs(skill_md)
        if (skill_md.parent / "scripts" / "pixelmap.py").exists():
            errors += check_map_library(skill_md) + check_map_renders(skill_md.parent)
    md_files = markdown_files()
    for md in md_files:
        errors += check_links(md)

    if errors:
        print(f"{len(errors)} problem(s):", file=sys.stderr)
        print("\n".join(f"- {e}" for e in errors), file=sys.stderr)
        return 1
    print(f"ok: {len(skill_files)} skill(s), {len(md_files)} Markdown file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
