# Compatibility

Every skill in this repo is a folder with a `SKILL.md` file, written in the [Agent Skills](https://agentskills.io/)
open format. Any agent that supports the format can load it as is: there are no per-agent versions to maintain and
nothing to convert.

## How agents load a skill

1. At startup, the agent reads only the `name` and `description` from each `SKILL.md`.
2. When your request matches a description, it reads the rest of that `SKILL.md`.
3. It opens the files in `scripts/`, `references/`, and `assets/` only when the instructions call for them.

## Installation options

The [skills](https://github.com/vercel-labs/skills) CLI is the package manager for the Agent Skills ecosystem. It
auto-detects your agent (s) and writes skills to each one's directory:

```bash
# Install step by step: the CLI asks which agents to use and whether to install for this project or your user
npx skills add rusocode/gamedev-skills

# See which skills the repo has, without installing anything
npx skills add rusocode/gamedev-skills --list

# Install one skill only
npx skills add rusocode/gamedev-skills --skill drawing-pixel-art

# Install for one agent, and make it available in all your projects
npx skills add rusocode/gamedev-skills -a claude-code -g
```

## Where each agent looks for skills

You rarely need this table, since the CLI picks the right folder. It helps if you prefer to copy a skill by hand.

| Agent          | User folder                   |
|----------------|-------------------------------|
| Claude Code    | `~/.claude/skills/`           |
| Codex          | `~/.codex/skills/`            |
| Cursor         | `~/.cursor/skills/`           |
| Gemini CLI     | `~/.gemini/skills/`           |
| GitHub Copilot | `~/.copilot/skills/`          |
| OpenCode       | `~/.config/opencode/skills/`  |
| Cline          | `~/.agents/skills/`           |
| Windsurf       | `~/.codeium/windsurf/skills/` |
| Kiro CLI       | `~/.kiro/skills/`             |

Inside a project, many agents share `.agents/skills/`, so a single copy there works for all of them. For the full list
of agents, see
the CLI's [supported agents](https://github.com/vercel-labs/skills#supported-agents) and the Agent Skills
[client list](https://agentskills.io/clients).

## Checking the installation

1. Run `npx skills list` to see the installed skills, or `/skills` in agents that have that command.
2. Ask for something the skill covers, like `Create a 16x16 key sprite`, and check that the agent follows the skill's
   steps instead of drawing on its own.

