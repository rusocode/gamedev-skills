# mis-skills

Colección de skills personales para Claude Code. Vive directamente en `~/.claude/skills/` (donde Claude las
descubre) para no necesitar symlinks. El `.gitignore` es una lista blanca: solo trackea las carpetas listadas
acá abajo, así que instalar una skill de terceros en este directorio no la mete al repo por accidente.

## Skills

- **drawing-pixel-art** — genera y edita sprites pixel art (32x32, etc.) para juegos 2D a partir de un mapa de
  caracteres, con validaciones de contorno, huecos y simetría. Ver `drawing-pixel-art/SKILL.md`.

## Agregar una skill nueva

1. Crear la carpeta `mi-skill-nueva/` con su `SKILL.md`.
2. Sumar al `.gitignore`:
   ```
   !/mi-skill-nueva/
   !/mi-skill-nueva/**
   ```
3. Sumarla a la lista de arriba.
