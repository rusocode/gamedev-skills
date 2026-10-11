import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import validate  # noqa: E402

VALID_SKILL = """---
name: demo-skill
description: >-
  Use when testing the validator.
  Second line of the description.
---

# Demo
"""


def temp_dir(test):
    """A fresh temp directory that is removed when the test finishes."""
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    return Path(tmp.name)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class FrontmatterTest(unittest.TestCase):
    def test_reads_plain_scalar(self):
        fields = validate.parse_frontmatter("---\nname: demo\ndescription: One line.\n---\nbody")
        self.assertEqual(fields, {"name": "demo", "description": "One line."})

    def test_folds_block_scalar_into_one_line(self):
        fields = validate.parse_frontmatter(VALID_SKILL)
        self.assertEqual(fields["description"], "Use when testing the validator. Second line of the description.")

    def test_returns_none_without_frontmatter(self):
        self.assertIsNone(validate.parse_frontmatter("# No frontmatter\n"))


class SkillFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = temp_dir(self)

    def check(self, folder, text):
        return validate.check_skill_file(write(self.tmp / folder / "SKILL.md", text))

    def test_valid_skill_has_no_errors(self):
        self.assertEqual(self.check("demo-skill", VALID_SKILL), [])

    def test_name_must_match_folder(self):
        errors = self.check("other-folder", VALID_SKILL)
        self.assertTrue(any("folder" in e for e in errors), errors)

    def test_name_must_be_lowercase_hyphenated(self):
        errors = self.check("Demo_Skill", VALID_SKILL.replace("demo-skill", "Demo_Skill"))
        self.assertTrue(any("lowercase" in e for e in errors), errors)

    def test_description_is_required(self):
        errors = self.check("demo-skill", "---\nname: demo-skill\n---\n")
        self.assertTrue(any("description" in e for e in errors), errors)

    def test_description_length_is_capped(self):
        long_text = VALID_SKILL.replace("Second line of the description.", "x" * 1100)
        errors = self.check("demo-skill", long_text)
        self.assertTrue(any("1024" in e for e in errors), errors)

    def test_body_length_is_capped(self):
        errors = self.check("demo-skill", VALID_SKILL + "line\n" * 500)
        self.assertTrue(any("lines" in e for e in errors), errors)


class LinkTest(unittest.TestCase):
    def setUp(self):
        self.tmp = temp_dir(self)
        write(self.tmp / "docs" / "guide.md", "# Guide\n")

    def test_reports_broken_relative_link(self):
        md = write(self.tmp / "README.md", "[ok](docs/guide.md) [broken](docs/missing.md)\n")
        errors = validate.check_links(md)
        self.assertEqual(len(errors), 1)
        self.assertIn("docs/missing.md", errors[0])

    def test_ignores_urls_anchors_and_code_blocks(self):
        md = write(self.tmp / "README.md",
                   "[web](https://example.com) [top](#top) [part](docs/guide.md#intro)\n"
                   "```\n[example](not/a/file.md)\n```\n")
        self.assertEqual(validate.check_links(md), [])

    def test_checks_html_image_sources(self):
        md = write(self.tmp / "README.md", '<img src="assets/missing.png">\n')
        self.assertEqual(len(validate.check_links(md)), 1)


class CodeReferenceTest(unittest.TestCase):
    def test_reports_missing_bundled_file(self):
        skill = temp_dir(self) / "demo-skill"
        write(skill / "scripts" / "tool.py", "")
        md = write(skill / "SKILL.md", "Run `scripts/tool.py`, then read `references/missing.md`.\n")
        errors = validate.check_code_refs(md)
        self.assertEqual(len(errors), 1)
        self.assertIn("references/missing.md", errors[0])


class MapLibraryTest(unittest.TestCase):
    def setUp(self):
        self.skill = temp_dir(self) / "demo-skill"
        write(self.skill / "assets" / "listed.txt", "")
        write(self.skill / "assets" / "unlisted.txt", "")

    def test_reports_maps_missing_from_the_table_and_rows_without_a_map(self):
        md = write(self.skill / "SKILL.md", "| `listed.txt` | ... |\n| `ghost.txt` | ... |\n")
        errors = validate.check_map_library(md)
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("unlisted.txt" in e for e in errors), errors)
        self.assertTrue(any("ghost.txt" in e for e in errors), errors)

    def test_reads_declared_variants(self):
        path = write(self.skill / "assets" / "potion.txt",
                     "# variante azul: R=1,2,3\n# variant green: R=4,5,6\n. = transparent\n")
        self.assertEqual(validate.map_variants(path), ["azul", "green"])


class TrimErrorLinesTest(unittest.TestCase):
    def lines(self, count):
        return [f"line {i}" for i in range(count)]

    def test_short_output_is_untouched(self):
        self.assertEqual(validate.trim_error_lines(self.lines(3)), self.lines(3))

    def test_long_error_keeps_its_head(self):
        trimmed = validate.trim_error_lines(["ERROR: bad map"] + self.lines(20))
        self.assertEqual(trimmed[0], "ERROR: bad map")
        self.assertEqual(len(trimmed), validate.RENDER_ERROR_LINES + 1)
        self.assertIn("more lines", trimmed[-1])

    def test_long_traceback_keeps_its_tail_where_the_exception_is(self):
        trimmed = validate.trim_error_lines(["Traceback (most recent call last):"] + self.lines(20)
                                            + ["RuntimeError: boom"])
        self.assertEqual(trimmed[-1], "RuntimeError: boom")
        self.assertEqual(len(trimmed), validate.RENDER_ERROR_LINES + 1)
        self.assertIn("more lines", trimmed[0])


if __name__ == "__main__":
    unittest.main()
