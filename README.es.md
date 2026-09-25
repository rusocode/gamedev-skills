<div align="center">

# ruso-skills

**Colección personal de skills para Claude Code y otros agentes de IA.**

![Claude Code](https://img.shields.io/badge/Claude%20Code-skills-D97757?logo=claude&logoColor=white)
![Último commit](https://img.shields.io/github/last-commit/rusocode/ruso-skills?color=2E7D32)

🌐 [English](README.md) | **Español**

</div>

---

## Skills

| Skill                                       | Descripción                                                                                                                                           | Requisitos       |
|---------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|------------------|
| [**drawing-pixel-art**](drawing-pixel-art/) | Crea y corrige sprites pixel art (16–64 px) para juegos 2D a partir de mapas de caracteres, validando contorno, huecos, simetría, encuadre y relieve. | Python 3, Pillow |

Cada skill tiene su propio README con uso, ejemplos y estructura.

## Instalación

Clonar el repositorio y copiar las skills que se quieran al directorio donde el agente las busca (`~/.claude/skills/`,
`~/.agents/skills/` o el que corresponda):

```bash
git clone https://github.com/rusocode/ruso-skills.git
cp -r ruso-skills/drawing-pixel-art ~/.claude/skills/
```

## Agregar una skill nueva

El [`.gitignore`](.gitignore) ignora todo por defecto, así el repositorio puede vivir directamente en
`~/.claude/skills/` junto a skills de terceros sin versionarlas. Cada skill se incluye de forma explícita:

1. Crear la carpeta `mi-skill-nueva/` con su `SKILL.md`.
2. Habilitarla en el `.gitignore`:
   ```gitignore
   !/mi-skill-nueva/
   ```
3. Sumarla a la tabla de [Skills](#-skills), tanto acá como en [`README.md`](README.md).
