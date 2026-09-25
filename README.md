<p align="right"><a href="README.es.md">🇪🇸</a></p>

<div align="left">

# ruso-skills

</div>

<div align="center">

![AI agents](https://img.shields.io/badge/AI%20agents-skills-D97757)
![Last commit](https://img.shields.io/github/last-commit/rusocode/ruso-skills?color=2E7D32)

</div>

A collection of skills for AI agents. Each skill is a self-contained package of instructions, scripts, and references
that gives an agent a specialized, repeatable workflow for a specific task. Skills work with any agent that supports
the skills format and are designed to produce consistent, verifiable results.

<br>

## Skills

Each skill lives in its own folder, with a `SKILL.md` that tells the agent when to use it and how. Agents load it
automatically when a request matches its description.

| Skill                                       | Description                                                                                                                                | Requirements     |
|---------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| [**drawing-pixel-art**](drawing-pixel-art/) | Creates and fixes pixel art sprites (16–64 px) for 2D games from character maps, validating outline, holes, symmetry, framing, and relief. | Python 3, Pillow |

Each skill has its own README with usage, examples, and structure.

## Installation

Clone the repository and copy the skills you want into the directory where your agent looks for them
(`~/.claude/skills/`, `~/.agents/skills/`, or the corresponding one):

```bash
git clone https://github.com/rusocode/ruso-skills.git
cp -r ruso-skills/drawing-pixel-art ~/.claude/skills/
```

## Adding a new skill

The [`.gitignore`](.gitignore) ignores everything by default, so the repository can live directly in
`~/.claude/skills/` next to third-party skills without tracking them. Each skill is included explicitly:

1. Create the `my-new-skill/` folder with its `SKILL.md`.
2. Whitelist it in `.gitignore`:
   ```gitignore
   !/my-new-skill/
   ```
3. Add it to the [Skills](#-skills) table, both here and in [`README.es.md`](README.es.md).
