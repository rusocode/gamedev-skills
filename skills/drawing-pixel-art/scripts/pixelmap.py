#!/usr/bin/env python
"""Character-map sprite tool: render a map to a pixel-perfect PNG, or rebuild a map from a PNG.

Map file format (UTF-8 text):

    # rasgo: bulbo redondo           '# rasgo:' / '# feature:' lines are echoed back as a checklist
    # relieve: especular 2x2 en (4,3) '# relieve:' / '# relief:' lines are the shading checklist, echoed back the same way
    # huecos: 0                      '# huecos: N' / '# holes: N' fails the render unless the silhouette has N enclosed holes
    # simetria: x                    '# simetria: x|y|xy' / '# symmetry:' fails unless the silhouette mirrors across that axis
    # espejo: x                      '# espejo: x|y|xy' / '# mirror:' draw only the left/top half; transparent cells on the
    #                                far half are filled from their twin (axis = canvas centre). Implies the symmetry check.
    # variante azul: R=40,96,225; r=22,48,150
    #                                '# variante nombre:' / '# variant name:' recolors those symbols when rendered with
    #                                --variant nombre; one grid, many colorways.
    . = transparent
    O = 28,18,26
    g = 200,220,240,150              optional alpha (default 255)

    (blank line ends the palette; every following non-empty line is one row)
    .......OOOO.......
    ......ORRRRO......

Symbols are case-sensitive. The symbol mapped to the word "transparent" is the background.

Usage:
    python scripts/pixelmap.py render   --map x.txt --out x.png [--width 32 --height 32] [--auto-outline] [--preview 8] [--variant azul]
    python scripts/pixelmap.py from-png --png x.png --out x.txt [--palette old.txt] [--variant azul]
    python scripts/pixelmap.py audit    --png x.png
"""
import argparse
import re
import sys
from collections import deque

from PIL import Image

PREVIEW_BG = (90, 110, 70, 255)
FLAT_CHECK_MIN_SIDE = 24    # smaller icons legitimately have few tones
FLAT_MIN_TONES = 6          # fill symbols (outline excluded) below this = flat
FLAT_MAX_DOMINANT = 40      # % of fill pixels in one tone above this = flat
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class MapError(Exception):
    pass


def parse_color(text):
    raw = re.split(r"\s*,\s*", text.strip())
    if len(raw) not in (3, 4):
        raise MapError(f"bad color '{text}' (expected R,G,B[,A])")
    try:
        parts = [int(p) for p in raw]
    except ValueError:
        raise MapError(f"bad color '{text}': every channel must be an integer 0-255")
    if any(p < 0 or p > 255 for p in parts):
        raise MapError(f"bad color '{text}': every channel must be 0-255")
    return (parts[0], parts[1], parts[2], parts[3] if len(parts) == 4 else 255)


def color_text(rgba):
    r, g, b, a = rgba
    return f"{r},{g},{b}" + (f",{a}" if a != 255 else "")


HEADER_RE = {
    "feature": re.compile(r"^\s*#\s*(?:feature|rasgo)\s*:\s*(.+?)\s*$"),
    "relief": re.compile(r"^\s*#\s*(?:relief|relieve)\s*:\s*(.+?)\s*$"),
    "bleed": re.compile(r"^\s*#\s*(?:bleed|sangra)\s*:\s*(?:si|s|yes|y|true)\s*$", re.I),
    "holes": re.compile(r"^\s*#\s*(?:holes|huecos)\s*:\s*(\d+)\s*$"),
    "symmetry": re.compile(r"^\s*#\s*(?:symmetry|simetria)\s*:\s*([xy]{1,2})\s*$", re.I),
    "mirror": re.compile(r"^\s*#\s*(?:mirror|espejo)\s*:\s*([xy]{1,2})\s*$", re.I),
    "variant": re.compile(r"^\s*#\s*(?:variant|variante)\s+(\S+)\s*:\s*(.+?)\s*$"),
}
PALETTE_RE = re.compile(r"^\s*(\S)\s*=\s*(.+?)\s*$")


def parse_map(path):
    """Returns dict: palette {sym: rgba}, transparent, rows, features, holes, symmetry, mirror, variants, header."""
    m = {"palette": {}, "transparent": None, "rows": [], "features": [], "relief": [], "bleed": False, "holes": None,
         "symmetry": "", "mirror": "", "variants": {}, "header": []}
    in_grid = False
    with open(path, encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.rstrip("\r\n")
            if not in_grid:
                if line.strip() == "":
                    if m["palette"]:
                        in_grid = True
                    continue
                if line.lstrip().startswith("#"):
                    m["header"].append(line)
                    if (mt := HEADER_RE["feature"].match(line)):
                        m["features"].append(mt.group(1))
                    elif (mt := HEADER_RE["relief"].match(line)):
                        m["relief"].append(mt.group(1))
                    elif HEADER_RE["bleed"].match(line):
                        m["bleed"] = True
                    elif (mt := HEADER_RE["holes"].match(line)):
                        m["holes"] = int(mt.group(1))
                    elif (mt := HEADER_RE["symmetry"].match(line)):
                        m["symmetry"] = mt.group(1).lower()
                    elif (mt := HEADER_RE["mirror"].match(line)):
                        m["mirror"] = mt.group(1).lower()
                    elif (mt := HEADER_RE["variant"].match(line)):
                        m["variants"][mt.group(1).lower()] = mt.group(2)
                    continue
                mt = PALETTE_RE.match(line)
                if not mt:
                    raise MapError(f"Bad palette line: '{line}'")
                sym, val = mt.group(1), mt.group(2)
                if val.lower() == "transparent":
                    m["transparent"] = sym
                else:
                    m["palette"][sym] = parse_color(val)
                continue
            if line.strip() == "":
                continue
            m["rows"].append(line)
    if m["transparent"] is None:
        raise MapError("Palette must declare a transparent symbol, e.g. '. = transparent'")
    if not m["rows"]:
        raise MapError("No grid rows found (palette must be followed by a blank line, then the rows)")
    return m


def apply_variant(palette, variants, name):
    key = name.lower()
    if key not in variants:
        raise MapError(f"variant '{name}' not declared in the map; known: {', '.join(sorted(variants)) or '(none)'}")
    changed = []
    for pair in re.split(r"\s*;\s*", variants[key].strip()):
        mt = re.match(r"^(\S)\s*=\s*(.+)$", pair)
        if not mt:
            raise MapError(f"bad variant entry '{pair}' (expected sym=R,G,B[,A])")
        sym = mt.group(1)
        if sym not in palette:
            raise MapError(f"variant '{name}' recolors '{sym}', which is not in the palette")
        palette[sym] = parse_color(mt.group(2))
        changed.append(sym)
    return changed


# ----------------------------------------------------------------------------- render

def flat_verdict(fill_counts):
    """Given {key: pixel_count} for the fill (outline/background excluded), returns
    (tones high-to-low, dominant key, dominant %, is_flat). `key` is usually a color. Shared by
    render's PLANO check and audit's FLAT verdict, so the two commands can't disagree about what
    counts as flat.
    """
    fill_total = sum(fill_counts.values())
    tones = sorted(fill_counts.items(), key=lambda kv: -kv[1])
    if not fill_total:
        return tones, None, 0, len(tones) < FLAT_MIN_TONES
    dom_key, dom_n = tones[0]
    dom_pct = round(100 * dom_n / fill_total)
    return tones, dom_key, dom_pct, len(tones) < FLAT_MIN_TONES or dom_pct > FLAT_MAX_DOMINANT


def make_is_transparent(grid, transparent, w, h):
    def is_transparent(x, y):
        return x < 0 or y < 0 or x >= w or y >= h or grid[y][x] == transparent
    return is_transparent


def build_grid(m, args):
    """Validates row widths against --width/--height and applies '# espejo', returning
    (grid, w, h, symmetry, mirror_note). `symmetry` folds in the mirror axis when the map declares
    no explicit '# simetria' of its own, since mirroring already guarantees it.
    """
    rows = m["rows"]
    w, h = len(rows[0]), len(rows)
    errors = [f"row {y} has width {len(r)}, expected {w}" for y, r in enumerate(rows) if len(r) != w]
    if args.width and w != args.width:
        errors.append(f"canvas width is {w}, expected {args.width} (pad rows with the transparent symbol)")
    if args.height and h != args.height:
        errors.append(f"canvas height is {h}, expected {args.height} (add transparent rows)")
    if errors:
        raise MapError("\n".join(errors))

    grid, transparent = [list(r) for r in rows], m["transparent"]
    symmetry, mirror_note = m["symmetry"], None
    if m["mirror"]:
        # Transparent cells on the far half take their twin from the near half; painted cells are kept.
        if "x" in m["mirror"]:
            for y in range(h):
                for x in range(w // 2):
                    mx = w - 1 - x
                    if grid[y][mx] == transparent:
                        grid[y][mx] = grid[y][x]
        if "y" in m["mirror"]:
            for y in range(h // 2):
                my = h - 1 - y
                for x in range(w):
                    if grid[my][x] == transparent:
                        grid[my][x] = grid[y][x]
        mirror_note = (f"mirror '{m['mirror']}': far half filled from the near half "
                       "(canvas centre is the axis, so centre the sprite)")
        if not symmetry:
            symmetry = m["mirror"]
    return grid, w, h, symmetry, mirror_note


def paint_pixels(grid, palette, transparent, is_transparent, w, h, args):
    """Paints the RGBA image and measures it in the same pass: fill tones by color (not by symbol,
    since two symbols can share a color), outline leaks, and the opaque bounding box.

    Returns (img, fill_count, fill_syms, leaks, bbox), bbox = (min_x, min_y, max_x, max_y) with
    max_x == -1 if the map has no opaque pixels.
    """
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = img.load()
    leaks, errors = [], []
    fill_count, fill_syms = {}, {}
    min_x, min_y, max_x, max_y = w, h, -1, -1
    for y in range(h):
        for x in range(w):
            ch = grid[y][x]
            if ch == transparent:
                continue
            if ch not in palette:
                errors.append(f"undeclared symbol '{ch}' at ({x},{y})")
                continue
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
            color = palette[ch]
            if ch != args.outline_symbol:
                edge = any(is_transparent(x + dx, y + dy) for dx, dy in DIRS)
                if edge:
                    if args.auto_outline:
                        color = palette[args.outline_symbol]
                    leaks.append(f"({x},{y}) '{ch}'")
            if color != palette.get(args.outline_symbol):
                fill_count[color] = fill_count.get(color, 0) + 1
                fill_syms.setdefault(color, set()).add(ch)
            px[x, y] = color
    if errors:
        raise MapError("\n".join(errors))
    return img, fill_count, fill_syms, leaks, (min_x, min_y, max_x, max_y)


def check_bounds(min_x, min_y, max_x, max_y, w, h, bleed):
    """Reports the sprite's bounding box, canvas coverage, and edge-margin warning."""
    bw, bh = max_x - min_x + 1, max_y - min_y + 1
    cov = round(100 * max(bw / w, bh / h))
    lines = [f"sprite bounds: cols {min_x}..{max_x}, rows {min_y}..{max_y} ({bw} x {bh}): "
             f"fills {cov}% of the canvas on its longest side"]
    if cov < 70:
        lines.append("WARNING: sprite uses under 70% of the canvas; enlarge the silhouette unless the sprite is meant to be small")
    if min_x == 0 or min_y == 0 or max_x == w - 1 or max_y == h - 1:
        if bleed:
            lines.append("bleed: sprite fills its cell to the edge, as declared")
        else:
            lines.append("WARNING: sprite touches the canvas edge; leave at least 1 px of margin "
                         "(a door, tile or backdrop that fills its cell declares '# sangra: si')")
    return lines


def report_flat_tones(fill_count, fill_syms, failures):
    """Reports the fill's tone breakdown (calibrated on 32x32 items: flat ones had 4 fill tones
    with 43-45% in one tone, detailed ones 7 tones and 33%) and appends any PLANO failure.
    """
    def label(color):
        return "/".join(sorted(fill_syms[color]))
    tones, dom_color, dom_pct, is_flat = flat_verdict(fill_count)
    fill_total = sum(n for _, n in tones)
    lines = [f"fill tones: {len(tones)} ("
             + " ".join(f"'{label(c)}'={round(100 * v / fill_total)}%" for c, v in tones)
             + f"); dominant '{label(dom_color)}' covers {dom_pct}% of the fill"]
    if len(tones) < FLAT_MIN_TONES:
        failures.append(f"PLANO: only {len(tones)} fill tones; a sprite this size needs at least {FLAT_MIN_TONES} "
                        "(ramp of 5-6 per material plus glint). Add tones, do not shrink the sprite.")
    if dom_pct > FLAT_MAX_DOMINANT:
        failures.append(f"PLANO: '{label(dom_color)}' covers {dom_pct}% of the fill (max {FLAT_MAX_DOMINANT}%); the faces are flat "
                        "blocks. Break them with ramp steps, dither at tone borders, glint, dimples and an inner dark rim.")
    return lines


def check_outline_leaks(leaks, args):
    """Reports the auto-outline count, or raises if leaks were left unhandled."""
    if args.auto_outline:
        return f"auto-outline: {len(leaks)} edge pixels painted as '{args.outline_symbol}'"
    if leaks and not args.no_validate:
        raise MapError(f"Outline leak: these non-outline pixels touch transparency. Make them '{args.outline_symbol}', "
                       "or re-run with --auto-outline (never merge separate pieces to silence this):\n  " + "\n  ".join(leaks))
    return None


def find_holes(is_transparent, w, h):
    """Flood-fills from the canvas border to mark the outside, then returns one description per
    remaining enclosed transparent region -- a ring, the gap between a bow and its string, a
    handle's opening.
    """
    seen = [[False] * w for _ in range(h)]
    queue = deque()
    for x in range(w):
        for y in (0, h - 1):
            if is_transparent(x, y) and not seen[y][x]:
                seen[y][x] = True
                queue.append((x, y))
    for y in range(h):
        for x in (0, w - 1):
            if is_transparent(x, y) and not seen[y][x]:
                seen[y][x] = True
                queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        for dx, dy in DIRS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and is_transparent(nx, ny):
                seen[ny][nx] = True
                queue.append((nx, ny))

    holes = []
    for y in range(h):
        for x in range(w):
            if seen[y][x] or not is_transparent(x, y):
                continue
            size, hx0, hy0, hx1, hy1 = 0, x, y, x, y
            seen[y][x] = True
            queue.append((x, y))
            while queue:
                cx, cy = queue.popleft()
                size += 1
                hx0, hx1, hy0, hy1 = min(hx0, cx), max(hx1, cx), min(hy0, cy), max(hy1, cy)
                for dx, dy in DIRS:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and is_transparent(nx, ny):
                        seen[ny][nx] = True
                        queue.append((nx, ny))
            holes.append(f"cols {hx0}..{hx1}, rows {hy0}..{hy1} ({size} px)")
    return holes


def report_holes(is_transparent, w, h, declared_holes, failures):
    """Runs find_holes() and returns its report line; appends a failure if the declared
    '# huecos' count doesn't match what the silhouette actually has.
    """
    holes = find_holes(is_transparent, w, h)
    line = (f"enclosed transparent holes: {len(holes)}"
            + (": " + "; ".join(holes) if holes else " (a ring, eye, handle or bow declared as a feature needs at least one)"))
    if declared_holes is not None and len(holes) != declared_holes:
        failures.append(f"declared '# holes: {declared_holes}' but the silhouette has {len(holes)}. "
                        "A hole is transparent pixels fully surrounded by opaque ones.")
    return line


def find_symmetry_mismatches(is_transparent, min_x, min_y, max_x, max_y, symmetry):
    """Returns '(x,y)' for each silhouette pixel with no mirror twin across `symmetry`'s axis/axes,
    counting each violating pair once (a plain scan visits and reports every pair from both sides).
    """
    mismatch, seen_pairs = [], set()
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            mx = min_x + max_x - x if "x" in symmetry else x
            my = min_y + max_y - y if "y" in symmetry else y
            if (x, y) == (mx, my):
                continue
            pair = frozenset({(x, y), (mx, my)})
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            if is_transparent(x, y) != is_transparent(mx, my):
                painted = (x, y) if not is_transparent(x, y) else (mx, my)
                mismatch.append(f"({painted[0]},{painted[1]})")
    return mismatch


def report_symmetry(is_transparent, min_x, min_y, max_x, max_y, symmetry, failures):
    """Returns the symmetry report line, or None (with the failure filed) when it fails."""
    if not symmetry:
        return None
    mismatch = find_symmetry_mismatches(is_transparent, min_x, min_y, max_x, max_y, symmetry)
    if not mismatch:
        return f"symmetry '{symmetry}': silhouette is mirror-symmetric"
    failures.append(f"declared '# symmetry: {symmetry}' but {len(mismatch)} silhouette pixels have no mirror twin: "
                    + " ".join(mismatch[:12]))
    return None


def report_checklists(m, bw, bh, failures):
    """Returns the '# rasgo'/'# relieve' checklists to verify against the preview, or files a
    failure when a sprite this size skipped '# relieve' declarations entirely.
    """
    lines = []
    if m["features"]:
        lines.append("CHECK each feature in the preview and state where it is (rows/cols) in your report:")
        lines.extend(f"  [ ] {f}" for f in m["features"])
    if m["relief"]:
        lines.append("CHECK each relief item in the preview (it must be visible at 8x, not just present in the map):")
        lines.extend(f"  [ ] {r}" for r in m["relief"])
    elif max(bw, bh) >= FLAT_CHECK_MIN_SIDE:
        failures.append("no '# relieve:' lines: declare the shading (ramp, glint, dither, dimples, inner rim) before rendering; "
                        "the map is the spec, the render is the check")
    return lines


def save_preview(img, args, w, h):
    big = img.resize((w * args.preview, h * args.preview), Image.NEAREST)
    bg = Image.new("RGBA", big.size, PREVIEW_BG)
    bg.alpha_composite(big)
    preview_path = re.sub(r"\.[^./\\]+$", "", args.out) + "_preview.png"
    bg.convert("RGB").save(preview_path, "PNG")
    return f"preview {preview_path} ({args.preview}x)"


def render(args):
    m = parse_map(args.map)
    palette, transparent = m["palette"], m["transparent"]
    out, failures = [], []

    if args.variant:
        out.append(f"variant '{args.variant}': recolored " + " ".join(apply_variant(palette, m["variants"], args.variant)))

    grid, w, h, symmetry, mirror_note = build_grid(m, args)
    if mirror_note:
        out.append(mirror_note)
    is_transparent = make_is_transparent(grid, transparent, w, h)

    if args.auto_outline and args.outline_symbol not in palette:
        raise MapError(f"--auto-outline needs '{args.outline_symbol}' in the palette")

    img, fill_count, fill_syms, leaks, (min_x, min_y, max_x, max_y) = paint_pixels(
        grid, palette, transparent, is_transparent, w, h, args)
    if max_x < 0:
        raise MapError("the map has no opaque pixels (every cell is the transparent symbol)")
    leak_note = check_outline_leaks(leaks, args)
    if leak_note:
        out.append(leak_note)

    img.save(args.out, "PNG")
    out.append(f"saved {args.out} ({w} x {h})")

    bw, bh = max_x - min_x + 1, max_y - min_y + 1
    out.extend(check_bounds(min_x, min_y, max_x, max_y, w, h, m["bleed"]))
    if fill_count and max(bw, bh) >= FLAT_CHECK_MIN_SIDE:
        out.extend(report_flat_tones(fill_count, fill_syms, failures))

    out.append(report_holes(is_transparent, w, h, m["holes"], failures))
    symmetry_note = report_symmetry(is_transparent, min_x, min_y, max_x, max_y, symmetry, failures)
    if symmetry_note:
        out.append(symmetry_note)

    out.extend(report_checklists(m, bw, bh, failures))
    if args.preview > 0:
        out.append(save_preview(img, args, w, h))

    print("\n".join(out))
    if failures:
        raise MapError("VALIDATION FAILED (files were still written so you can inspect the preview):\n  " + "\n  ".join(failures))


# ----------------------------------------------------------------------------- from-png

def from_png(args):
    """Rebuild a map from a PNG so a sprite edited in an image editor becomes the source again."""
    sym_color = {}          # symbol -> rgba as declared (variant applied)
    header = []
    transparent = args.transparent_symbol
    old_palette_lines = []
    variant_syms = set()    # symbols any '# variant:' line recolors; keep them even if unused in this PNG
    if args.palette:
        old = parse_map(args.palette)
        header = old["header"]
        transparent = old["transparent"]
        base_palette = dict(old["palette"])
        sym_color = dict(base_palette)
        if args.variant:
            apply_variant(sym_color, old["variants"], args.variant)
        old_palette_lines = list(old["palette"].keys())
        for spec in old["variants"].values():
            variant_syms.update(re.findall(r"(\S)\s*=", spec))
    by_color = {rgba: sym for sym, rgba in sym_color.items()}
    used = set(sym_color) | {transparent}

    img = Image.open(args.png).convert("RGBA")
    w, h = img.size
    px = img.load()
    rows, order, snapped, next_idx = [], [], 0, 0
    for y in range(h):
        row = []
        for x in range(w):
            c = px[x, y]
            if c[3] == 0:
                row.append(transparent)
                continue
            if c not in by_color and args.tolerance > 0:
                # Editors and GDI+ round translucent colors by a unit or two; snap those to the existing symbol.
                for known, sym in list(by_color.items()):
                    if max(abs(a - b) for a, b in zip(known, c)) <= args.tolerance:
                        by_color[c] = sym
                        snapped += 1
                        break
            if c not in by_color:
                sym = None
                if args.outline_symbol not in used and c[0] + c[1] + c[2] < 120:
                    sym = args.outline_symbol
                while sym is None:
                    if next_idx >= len(args.alphabet):
                        raise MapError(f"more than {len(args.alphabet)} colors; reduce the palette first")
                    cand = args.alphabet[next_idx]
                    next_idx += 1
                    if cand not in used:
                        sym = cand
                by_color[c] = sym
                used.add(sym)
                order.append(c)
                if len(order) > args.max_new_colors:
                    sample = " | ".join(color_text(o) if o[3] != 255 else ",".join(map(str, o)) for o in order[:6])
                    raise MapError(f"more than {args.max_new_colors} colors are not in the palette: the PNG looks anti-aliased or has "
                                   "partial-alpha layers. Not writing a map. Fix the source first: in Aseprite use a pencil without "
                                   "antialias, flatten layers, and Sprite > Color Mode > Indexed keeps the palette exact. "
                                   f"Sample of unknown colors: {sample}")
            row.append(by_color[c])
        rows.append("".join(row))

    present = {ch for r in rows for ch in r}
    lines = list(header)
    lines.append(f"{transparent} = transparent")
    dropped, kept_for_variant = [], []
    for sym in old_palette_lines:
        if sym in present:
            lines.append(f"{sym} = {color_text(base_palette[sym])}")
        elif sym in variant_syms:
            lines.append(f"{sym} = {color_text(base_palette[sym])}")
            kept_for_variant.append(sym)
        else:
            dropped.append(sym)
    for c in order:
        lines.append(f"{by_color[c]} = {color_text(c)}")
    lines.append("")
    lines.extend(rows)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")

    opaque_syms = present - {transparent}
    print(f"wrote {args.out} ({w} x {h}, {len(opaque_syms)} colors, {len(order)} new symbols)")
    if snapped:
        print(f"snapped {snapped} off-by-<={args.tolerance} colors to their existing palette symbol (editor/GDI+ rounding)")
    if order:
        print("new colors got symbols: " + " ".join(f"{by_color[c]}={color_text(c)}" for c in order)
              + "; rename them to something meaningful if they replace an old tone")
    if kept_for_variant:
        print("kept unused palette symbols because a '# variant:' line still recolors them: " + " ".join(kept_for_variant))
    if dropped:
        print("dropped palette symbols no longer used in the PNG: " + " ".join(dropped))
    if header:
        print("kept header declarations from the old map; render to confirm '# huecos'/'# simetria' still hold")


# ----------------------------------------------------------------------------- audit

def audit(args):
    """Measure an existing PNG against the skill's contract and say which mode fits.

    Answers the question you have before touching an existing sprite: is this authored pixel art
    that can be reopened as a map, or a painted/downscaled image that has to be redrawn?
    """
    img = Image.open(args.png).convert("RGBA")
    w, h = img.size
    get = img.load()
    px = [get[x, y] for y in range(h) for x in range(w) if get[x, y][3] > 0]
    if not px:
        raise MapError(f"{args.png} is fully transparent")
    counts = {}
    for p in px:
        counts[p] = counts.get(p, 0) + 1
    once = sum(1 for v in counts.values() if v == 1)
    semi = sum(1 for p in px if p[3] < 255)

    def opaque(x, y):
        return 0 <= x < w and 0 <= y < h and get[x, y][3] > 0
    edge = [get[x, y] for y in range(h) for x in range(w)
            if get[x, y][3] > 0 and not all(opaque(x + dx, y + dy) for dx, dy in DIRS)]
    def lum(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    edge_lum = sorted(lum(c) for c in edge)
    edge_med = edge_lum[len(edge_lum) // 2]
    edge_max = edge_lum[-1]
    # The outline is the darkest colour; everything else is fill.
    outline = min(counts, key=lambda c: lum(c))
    fill = {c: n for c, n in counts.items() if c != outline}
    tones, _, dom_pct, flat = flat_verdict(fill)

    xs = [x for y in range(h) for x in range(w) if get[x, y][3] > 0]
    ys = [y for y in range(h) for x in range(w) if get[x, y][3] > 0]
    bw, bh = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    cov = round(100 * max(bw / w, bh / h))

    out = [f"{args.png}: {w}x{h}, {len(px)} opaque px, bbox {bw}x{bh} ({cov}% of the canvas)",
           f"colours: {len(counts)} ({once} used by a single pixel, {semi} semi-transparent)",
           f"fill tones: {len(tones)}, dominant covers {dom_pct}%",
           f"edge pixels: {len(edge)}, median luminance {edge_med:.0f}, brightest {edge_max:.0f}"]

    authored = len(counts) <= args.max_colors and once <= len(counts) * 0.15
    has_outline = edge_med <= 90

    verdict = []
    if not authored:
        verdict.append(f"PAINTED: {len(counts)} colours, {once} of them used once. This was made with a soft brush "
                       "or downscaled from a bigger image, not placed pixel by pixel. 'from-png' will refuse it and "
                       "it is not a style reference -- only a reference for WHAT the object is.")
    if not has_outline:
        verdict.append(f"NO OUTLINE: the border's median luminance is {edge_med:.0f} (brightest {edge_max:.0f}); "
                       "the sprite dissolves into the background. Step 6.")
    if flat:
        verdict.append(f"FLAT: {len(tones)} fill tones, dominant {dom_pct}% "
                       f"(needs >= {FLAT_MIN_TONES} tones and <= {FLAT_MAX_DOMINANT}%). Step 7.")
    if cov < 70:
        verdict.append(f"SMALL: fills {cov}% of the canvas. Step 3.")

    if not verdict:
        out.append("VERDICT: meets the contract. Nothing to fix unless the drawing itself is wrong.")
    elif authored:
        out.append("VERDICT: authored pixel art -> RETOUCH. Rebuild the map with 'from-png', fix it there and "
                   "re-render; everything you do not touch stays identical pixel for pixel.")
        out.extend("  - " + v for v in verdict)
    else:
        out.append("VERDICT: not reopenable as a map -> REDRAW. Ask whether the silhouette is worth keeping: if the "
                   "composition reads, copy it and redraw the shading; if it does not, redesign from scratch.")
        out.extend("  - " + v for v in verdict)
    print(chr(10).join(out))


# ----------------------------------------------------------------------------- cli

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("render", help="map -> PNG (+ validation, preview)")
    r.add_argument("--map", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--preview", type=int, default=0, help="also write <out>_preview.png scaled N times over a green background")
    r.add_argument("--width", type=int, default=0, help="fail unless the map is exactly this wide")
    r.add_argument("--height", type=int, default=0, help="fail unless the map is exactly this tall")
    r.add_argument("--outline-symbol", default="O")
    r.add_argument("--variant", default="", help="apply a '# variante nombre:' recolor")
    r.add_argument("--auto-outline", action="store_true", help="paint every pixel touching transparency with the outline symbol")
    r.add_argument("--no-validate", action="store_true", help="do not fail on outline leaks")
    r.set_defaults(func=render)

    f = sub.add_parser("from-png", help="PNG -> map (reuse an old map's palette and header)")
    f.add_argument("--png", required=True)
    f.add_argument("--out", required=True)
    f.add_argument("--palette", default="", help="existing map whose symbols and header lines are reused")
    f.add_argument("--variant", default="", help="the PNG is this variant of --palette")
    f.add_argument("--alphabet", default="abcdefhijkmnopqrstuvxyzABCDEFHIJKLMNPQRSTUVWXYZ")
    f.add_argument("--transparent-symbol", default=".")
    f.add_argument("--outline-symbol", default="O")
    f.add_argument("--tolerance", type=int, default=2, help="max per-channel distance to reuse an existing symbol")
    f.add_argument("--max-new-colors", type=int, default=32, help="refuse when more colors than this are unknown (anti-aliasing)")
    f.set_defaults(func=from_png)

    a = sub.add_parser("audit", help="measure an existing PNG and say whether to retouch or redraw it")
    a.add_argument("--png", required=True)
    a.add_argument("--max-colors", type=int, default=32, help="above this many colours a PNG is treated as painted")
    a.set_defaults(func=audit)

    args = p.parse_args(argv)
    try:
        args.func(args)
    except MapError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        # missing/unreadable map or PNG, missing output directory, corrupt image: report it, not a traceback
        print(f"ERROR: {e.strerror or e}: '{e.filename}'" if e.filename else f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
