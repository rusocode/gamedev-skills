#!/usr/bin/env python
"""Dos ayudas para siluetas con reborde perimetral. NO dibujan: preparan el andamiaje.

La silueta sigue siendo tuya y se escribe a mano como tabla de spans `fila -> (col_inicio, col_fin)`,
copiando las curvas de `references/shapes.md`. Lo que este modulo evita es medir a ojo dos cosas que se
calculan mejor:

  bands(spans, w, h)  -> (solid, layer). layer[y][x] es la distancia en 4-vecinos al primer pixel
                         transparente: 1 = contorno, 2..k = reborde, k+1 = ranura, resto = campo.
                         Da el reborde de ancho constante que siguiendo el contorno a mano sale
                         mas fino en las diagonales (3 px horizontales sobre un borde a 45 grados
                         son 2.1 px perpendiculares).

  bevel_index(...)    -> indice de rampa para un pixel de reborde, segun cuanto mira su normal
                         hacia la luz. Es lo que hace que un reborde se lea como bisel levantado
                         (claro arriba-izquierda, medio en los flancos, oscuro abajo-derecha) en vez
                         de como una banda plana del mismo tono.

El campo, el sombreado, los remaches y la textura se escriben a mano encima: ahi esta el dibujo.
Ver `assets/iron_shield.txt` y su reconstruccion en el paso 9 de SKILL.md.

Uso tipico:

    from bands import bands, bevel_index

    RAMP = ['D', 'd', 'n', 'm', 'l', 'L']          # oscuro -> claro
    solid, layer = bands(SPANS, 32, 32)
    grid = [['.'] * 32 for _ in range(32)]
    for y in range(32):
        for x in range(32):
            if not solid[y][x]:
                continue
            lay = layer[y][x]
            if lay == 1:                            # contorno (o dejarlo a --auto-outline)
                grid[y][x] = 'O'
            elif lay in (2, 3):                     # reborde de 2 px
                i = bevel_index(x, y, solid, lo=1, hi=5)
                grid[y][x] = RAMP[max(1, i - 1) if lay == 3 else i]
            elif lay == 4:                          # ranura que separa reborde y campo
                grid[y][x] = 'D'
            else:
                grid[y][x] = ...                    # el campo, a mano
"""
import math

DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
LIGHT_UPPER_LEFT = (-0.7071, -0.7071)


def bands(spans, width, height):
    """Silueta + capas concentricas a partir de una tabla `fila -> (col_inicio, col_fin)`.

    Devuelve `(solid, layer)`, ambas matrices `[y][x]`. `solid` es booleana; `layer` vale 0 en lo
    transparente, 1 en el contorno y sube hacia adentro. Las columnas del span son inclusivas.
    """
    solid = [[False] * width for _ in range(height)]
    for y, (a, b) in spans.items():
        if not 0 <= y < height:
            raise ValueError(f"fila {y} fuera del lienzo de {height}")
        if not 0 <= a <= b < width:
            raise ValueError(f"span ({a},{b}) invalido en la fila {y} para un ancho de {width}")
        for x in range(a, b + 1):
            solid[y][x] = True

    far = width + height
    layer = [[far if solid[y][x] else 0 for x in range(width)] for y in range(height)]
    changed = True
    while changed:                                  # relajacion hasta punto fijo: lienzos chicos, sobra
        changed = False
        for y in range(height):
            for x in range(width):
                if not solid[y][x]:
                    continue
                best = far
                for dx, dy in DIRS:
                    nx, ny = x + dx, y + dy
                    inside = 0 <= nx < width and 0 <= ny < height and solid[ny][nx]
                    best = min(best, (layer[ny][nx] if inside else 0) + 1)
                if best < layer[y][x]:
                    layer[y][x] = best
                    changed = True
    return solid, layer


def bevel_index(x, y, solid, lo, hi, light=LIGHT_UPPER_LEFT, radius=6):
    """Indice de rampa en `[lo, hi]` para un pixel de reborde, por la normal de la superficie.

    La normal sale del pixel hacia el transparente mas cercano dentro de `radius`. Su producto punto
    con `light` da -1 (de espaldas a la luz) a 1 (de frente), que se reparte en los escalones
    disponibles. Reservar el tono mas oscuro de la rampa para las ranuras y el campo en sombra
    pasando `lo=1`: si el reborde tambien llega a el, la ranura deja de leerse.
    """
    height, width = len(solid), len(solid[0])
    best, best_d2 = None, None
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and solid[ny][nx]:
                continue
            d2 = dx * dx + dy * dy                  # el transparente mas cercano, tambien fuera del lienzo
            if best_d2 is None or d2 < best_d2:
                best_d2, best = d2, (nx - x, ny - y)
    if best is None:
        return hi                                   # mas hondo que `radius`: no es reborde
    vx, vy = best
    norm = math.hypot(vx, vy) or 1.0
    dot = (vx / norm) * light[0] + (vy / norm) * light[1]
    steps = hi - lo + 1
    return max(lo, min(hi, lo + int((dot + 1) / 2 * steps)))
