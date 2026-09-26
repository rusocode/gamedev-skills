# gamedev-skills

A collection of game development skills for AI coding agents. Skills are packaged instructions and scripts that extend
agent capabilities.

Skills follow the [Agent Skills](https://agentskills.io/) format.

## Available Skills

### [drawing-pixel-art](drawing-pixel-art/)

Draws and fixes pixel art sprites (16–64 px) that are recognizable at a glance. Every sprite is checked before you get
the PNG, so you don't end up with flat or broken shapes.

**Use when:**

- Creating a new sprite, icon, item, or tile
- Fixing a sprite that's unrecognizable, has broken edges, is too small on the canvas, or looks flat
- Making a specific change to an existing sprite
- Adding a color variant of a sprite
- Syncing a sprite's map after editing the PNG by hand

## Installation

With the [`skills`](https://github.com/vercel-labs/skills) CLI (requires Node.js):

```bash
npx skills add rusocode/gamedev-skills
```

## Usage

Skills are automatically available once installed. The agent will use them when relevant tasks are detected.

**Examples:**

```
Create a 32x32 torch sprite
```

```
Fix the sword.png sprite
```

## Skill Structure

Each skill contains:

- `SKILL.md` - Instructions for the agent
- `scripts/` - Helper scripts for automation (optional)
- `references/` - Supporting documentation (optional)
- `assets/` - Templates and static resources (optional)

## License

[MIT](LICENSE)