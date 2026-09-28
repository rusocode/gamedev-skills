import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "drawing-pixel-art" / "scripts"))

import pixelmap  # noqa: E402


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run_main(argv):
    """Runs pixelmap.main() and captures stdout/stderr instead of letting them hit the terminal."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = pixelmap.main(argv)
    return code, out.getvalue(), err.getvalue()


class ParseColorTest(unittest.TestCase):
    def test_parses_rgb_and_rgba(self):
        self.assertEqual(pixelmap.parse_color("1,2,3"), (1, 2, 3, 255))
        self.assertEqual(pixelmap.parse_color("1,2,3,4"), (1, 2, 3, 4))

    def test_rejects_out_of_range_channel_instead_of_silently_clamping(self):
        with self.assertRaises(pixelmap.MapError):
            pixelmap.parse_color("300,-5,0")

    def test_rejects_non_numeric_channel_with_a_map_error_not_a_traceback(self):
        with self.assertRaises(pixelmap.MapError):
            pixelmap.parse_color("1,2,x")


class RenderErrorHandlingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_missing_map_file_is_a_clean_error_not_a_traceback(self):
        code, _, err = run_main(["render", "--map", str(self.tmp / "nope.txt"), "--out", str(self.tmp / "o.png")])
        self.assertEqual(code, 1)
        self.assertTrue(err.strip().startswith("ERROR:"), err)
        self.assertNotIn("Traceback", err)

    def test_missing_output_directory_is_a_clean_error_not_a_traceback(self):
        map_path = write(self.tmp / "ok.txt", ". = transparent\nO = 1,2,3\n\n...\n.O.\n...\n")
        code, _, err = run_main(["render", "--map", str(map_path), "--out", str(self.tmp / "nodir" / "o.png")])
        self.assertEqual(code, 1)
        self.assertTrue(err.strip().startswith("ERROR:"), err)
        self.assertNotIn("Traceback", err)

    def test_out_of_range_color_in_a_map_fails_cleanly(self):
        map_path = write(self.tmp / "bad.txt", ". = transparent\nO = 300,-5,0\n\n...\n.O.\n...\n")
        code, _, err = run_main(["render", "--map", str(map_path), "--out", str(self.tmp / "o.png")])
        self.assertEqual(code, 1)
        self.assertIn("300", err)

    def test_fully_transparent_map_is_rejected_instead_of_skipping_declared_checks(self):
        map_path = write(self.tmp / "empty.txt",
                          "# huecos: 2\n# simetria: x\n. = transparent\nO = 1,2,3\n\n....\n....\n")
        code, _, err = run_main(["render", "--map", str(map_path), "--out", str(self.tmp / "o.png")])
        self.assertEqual(code, 1)
        self.assertIn("no opaque", err.lower())


class SymmetryReportTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_one_asymmetric_pixel_is_reported_once_not_twice(self):
        # row 2 is missing its rightmost column, every other row is a symmetric block
        map_path = write(self.tmp / "sym.txt",
                          "# simetria: x\n. = transparent\nO = 1,2,3\n\n"
                          ".......\n.OOOOO.\n.OOOO..\n.OOOOO.\n.......\n")
        code, _, err = run_main(["render", "--map", str(map_path), "--out", str(self.tmp / "o.png")])
        self.assertEqual(code, 1)
        self.assertIn("1 silhouette pixels", err)


class FlatCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_plano_check_counts_distinct_colors_not_distinct_symbols(self):
        # 6 symbols, identical color: a real ramp needs 6 distinct COLORS, not 6 letters.
        syms = "abcdef"
        palette = "".join(f"{s} = 100,100,100\n" for s in syms)
        rows = ["." * 28]
        for y in range(26):
            rows.append("." + "".join(syms[(x + y) % 6] for x in range(26)) + ".")
        rows.append("." * 28)
        map_path = write(self.tmp / "alias.txt", f". = transparent\nO = 1,1,1\n{palette}\n" + "\n".join(rows) + "\n")
        code, out, err = run_main(["render", "--map", str(map_path), "--out", str(self.tmp / "o.png"),
                                    "--auto-outline"])
        self.assertEqual(code, 1)
        self.assertIn("PLANO", out + err)


class AuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_single_tone_sprite_gets_a_verdict_instead_of_crashing(self):
        img_path = self.tmp / "mono.png"
        im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        for y in range(4, 12):
            for x in range(4, 12):
                im.putpixel((x, y), (30, 30, 30, 255))
        im.save(img_path)
        code, out, err = run_main(["audit", "--png", str(img_path)])
        self.assertEqual(code, 0, err)
        self.assertNotIn("Traceback", err)
        self.assertIn("VERDICT", out)
        # a sprite with zero fill tones (the whole shape is a single color) IS flat, not exempt from the check
        self.assertIn("FLAT", out)


class FromPngTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_keeps_palette_symbols_still_referenced_by_a_variant(self):
        base = write(self.tmp / "pot.txt",
                      "# variante azul: R=0,0,200; b=100,100,255\n. = transparent\nO = 20,20,20\n"
                      "R = 200,0,0\nb = 255,200,200\n\n.....\n.ORb.\n.ORR.\n.....\n")
        png = self.tmp / "pot.png"
        code, _, err = run_main(["render", "--map", str(base), "--out", str(png), "--auto-outline"])
        self.assertEqual(code, 0, err)

        # simulate a hand edit that removes every pixel of symbol 'b' (repainted as 'R')
        im = Image.open(png).convert("RGBA")
        for y in range(im.height):
            for x in range(im.width):
                if im.getpixel((x, y))[:3] == (255, 200, 200):
                    im.putpixel((x, y), (200, 0, 0, 255))
        edited = self.tmp / "pot_edit.png"
        im.save(edited)

        rebuilt = self.tmp / "pot2.txt"
        code, _, err = run_main(["from-png", "--png", str(edited), "--palette", str(base), "--out", str(rebuilt)])
        self.assertEqual(code, 0, err)

        # the variant must still render: 'b' is unused now, but the variant declaration still names it
        code, _, err = run_main(["render", "--map", str(rebuilt), "--out", str(self.tmp / "p2.png"),
                                  "--variant", "azul", "--auto-outline"])
        self.assertEqual(code, 0, err)

    def test_counts_colors_correctly_for_a_fully_opaque_image(self):
        img_path = self.tmp / "tile.png"
        im = Image.new("RGBA", (4, 4), (200, 100, 50, 255))
        im.putpixel((0, 0), (10, 10, 10, 255))
        im.save(img_path)
        out_path = self.tmp / "tile.txt"
        code, out, err = run_main(["from-png", "--png", str(img_path), "--out", str(out_path)])
        self.assertEqual(code, 0, err)
        self.assertIn("2 colors", out)


if __name__ == "__main__":
    unittest.main()
