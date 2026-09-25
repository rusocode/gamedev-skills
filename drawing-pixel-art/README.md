# Drawing Pixel Art

Draws and fixes pixel art sprites (16–64 px) that are recognizable at a glance. Every sprite is checked before you get
the PNG, so you don't end up with flat or broken shapes.

<p align="center"><img src="example.png" width="560"></p>

## Requirements

- Node.js, to install the skill with the [`skills`](https://github.com/vercel-labs/skills) CLI
- Python 3, to run the skill's scripts

## Installation

```bash
# Install the skill
npx skills add rusocode/ruso-skills --skill drawing-pixel-art

# Install Pillow, the image library the skill's scripts use
pip install pillow
```

## How It Works

1. The agent writes the sprite as a **map**: a text grid where each character is one pixel of one color.
2. A script turns the map into a PNG and checks its outline, symmetry, framing, and shading. If a check fails, the
   agent fixes the map before showing you anything.
3. You get the PNG with an **8x enlarged preview**, in a drafts folder away from your game's assets.
4. **Nothing enters your project until you approve it.** Then the PNG goes to your textures folder, and its map joins
   the skill's library of approved sprites, so similar sprites don't start from scratch.

## Recommended Model

Use the most capable model your agent offers, with extended reasoning on (for example, Claude Opus). The checks catch
broken or flat sprites, but not whether the drawing is good, so a less capable model can deliver sprites that pass
every check and still look bland.

Tested on the same task with two Claude models, fixing a 32x32 wooden shield while keeping its shape:

|                         | Sonnet | Opus |
|-------------------------|:------:|:----:|
| Passes every check      |  yes   | yes  |
| Shades on the metal rim |   3    |  7   |
| Rivets                  |   0    |  8   |
| Wood grain lines        |   0    |  8   |

> [!TIP]
> If a sprite comes out correct but bland, check which model you used before asking for changes.

## Usage

| What you want                        | Prompt                                       |
|--------------------------------------|----------------------------------------------|
| A new sprite                         | `Create a 32x32 torch sprite`                |
| Fix an existing one                  | `Fix the sword.png sprite`                   |
| A specific change to an existing one | `Remove the little rock from stone.png`      |
| A different color of the same sprite | `Add a green variant of the potion`          |
| Keep edits you made in an editor     | `I edited sword.png by hand, update its map` |

Details worth keeping in mind:

- **Say "sprite", "texture", "item", or "icon"** somewhere: that's what triggers the skill.
- **The size isn't necessary** if the sprite already exists: it comes from the file.

### Fixing an Existing Sprite

Ask to fix it, without saying "touch up" or "redraw": the skill measures the sprite first and picks the approach.

- **If it's clean pixel art**, drawn pixel by pixel with few colors, it fixes only what's wrong, and everything else
  stays exactly as it was.
- **If it only looks like pixel art**, like a bigger image scaled down or one drawn with a soft brush (dozens of
  colors, blurry edges, like the "before" shield above), it has to redraw it. Before starting, it asks whether to
  keep the same shape or redesign it. You can answer in advance: `…, keeping the silhouette` or
  `…, the silhouette can change`.

You don't need to point out extra colors, a missing outline, flat shading, or a sprite that's too small on the canvas:
the skill detects those on its own. Do explain when the problem is the drawing itself, because no check catches that:

- *"can't tell what this is"*
- *"the silhouette is wrong, don't use it as a reference"*
- *"the pose is off"*
- *"the coins look like cookies"*

## Structure

```
drawing-pixel-art/
├── SKILL.md         # Instructions for the agent: the step-by-step drawing process
├── scripts/
│   ├── pixelmap.py  # Turns maps into PNGs, checks them, and audits existing sprites
│   └── bands.py     # Helper for even rims on shields, coins, and doors
├── examples/        # Approved maps: the library new sprites start from
└── references/
    └── shapes.md    # Ready-made circles by diameter, for round shapes
```
