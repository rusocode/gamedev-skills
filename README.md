# gamedev-skills

A collection of game development skills for AI coding agents.

## Available skills

### [drawing-pixel-art](skills/drawing-pixel-art/)

Draws and fixes pixel art sprites (16–64 px) that are recognizable at a glance. Every sprite is checked before you get
the PNG, so you don't end up with flat or broken shapes.

**Use when:**

- Creating a new sprite, icon, item, or tile
- Fixing a sprite that's unrecognizable, has broken edges, is too small on the canvas, or looks flat
- Making a specific change to an existing sprite
- Adding a color variant of a sprite
- Syncing a sprite's map after editing the PNG by hand

## Installation

**One command, any agent.** The [skills](https://github.com/vercel-labs/skills) CLI
(requires [Node.js](https://nodejs.org/en/download)) detects the coding agent you already use and installs the skills
into the right place:

```bash
npx skills add rusocode/gamedev-skills
```

Add `--list` to see the skills before installing, `-g` to make them available in all your projects, or `-a <agent>` to
install for one agent only (`-a claude-code`, `-a codex`, `-a cursor`, …). The same `SKILL.md` files load natively in
Claude Code, Cursor, Windsurf, Cline, Codex, Gemini CLI, GitHub Copilot, Kiro, and [many more](docs/COMPATIBILITY.md) —
there's nothing to convert.

Then just talk to your agent — see below.

## What you can ask

Describe what you need in plain language. The agent picks the right skill from your request:

| You say                                      | What you get                                                        |
|----------------------------------------------|---------------------------------------------------------------------|
| "create a 32x32 torch sprite"                | A new sprite, already checked, as a draft for you to approve        |
| "fix the sword.png sprite"                   | The sprite measured first, then fixed or redrawn depending on state |
| "remove the little rock from stone.png"      | Only that change, with the rest of the sprite left as it was        |
| "add a green variant of the potion"          | The same sprite in a different color                                |
| "I edited sword.png by hand, update its map" | Its map synced with your edits, so later changes keep them          |

You never type the skill's name. Mentioning "sprite", "texture", "item", or "icon" is enough for the agent to use it.

## Skill structure

Each skill contains:

- `SKILL.md` - Instructions for the agent
- `scripts/` - Helper scripts for automation (optional)
- `references/` - Supporting documentation (optional)
- `assets/` - Templates and static resources (optional)

## License

[MIT](LICENSE)