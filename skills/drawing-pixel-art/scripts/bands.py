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
Ver `assets/iron_shield.txt` (ejemplo completo) y la seccion "Herramienta" de SKILL.md.

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

    # Distancia exacta (4-vecinos) al transparente u borde de lienzo mas cercano, en dos barridos
    # (Rosenfeld & Pfaltz): ida (arriba-izquierda) mirando arriba/izquierda, vuelta (abajo-derecha)
    # mirando abajo/derecha. Cada pixel transparente ya vale 0, asi que el borde del lienzo actua
    # como limite implicito sin necesitar relajacion hasta punto fijo.
    layer = [[0] * width for _ in range(height)]
    for y in range(height):
        for x in range(width):
            if not solid[y][x]:
                continue
            up = layer[y - 1][x] if y > 0 else 0
            left = layer[y][x - 1] if x > 0 else 0
            layer[y][x] = min(up, left) + 1
    for y in range(height - 1, -1, -1):
        for x in range(width - 1, -1, -1):
            if not solid[y][x]:
                continue
            down = layer[y + 1][x] if y < height - 1 else 0
            right = layer[y][x + 1] if x < width - 1 else 0
            layer[y][x] = min(layer[y][x], down + 1, right + 1)
    return solid, layer


def bevel_index(x, y, solid, lo, hi, light=LIGHT_UPPER_LEFT, radius=6):
    """Indice de rampa en `[lo, hi]` para un pixel de reborde, por la normal de la superficie.

    La normal sale del pixel hacia el promedio de los transparentes mas cercanos dentro de `radius`
    (una esquina suele tener dos, a la misma distancia y en direcciones distintas; promediarlas evita
    que el orden de barrido elija una sola y sesgue el resultado hacia esa direccion). Su producto
    punto con `light` da -1 (de espaldas a la luz) a 1 (de frente), que se reparte en los escalones
    disponibles. Reservar el tono mas oscuro de la rampa para las ranuras y el campo en sombra
    pasando `lo=1`: si el reborde tambien llega a el, la ranura deja de leerse.
    """
    height, width = len(solid), len(solid[0])
    best_d2, ties = None, []
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and solid[ny][nx]:
                continue
            d2 = dx * dx + dy * dy                  # el transparente mas cercano, tambien fuera del lienzo
            if best_d2 is None or d2 < best_d2:
                best_d2, ties = d2, [(dx, dy)]
            elif d2 == best_d2:
                ties.append((dx, dy))
    if best_d2 is None:
        return hi                                   # mas hondo que `radius`: no es reborde
    vx = sum(dx for dx, _ in ties) / len(ties)
    vy = sum(dy for _, dy in ties) / len(ties)
    norm = math.hypot(vx, vy) or 1.0
    dot = (vx / norm) * light[0] + (vy / norm) * light[1]
    steps = hi - lo + 1
    return max(lo, min(hi, lo + int((dot + 1) / 2 * steps)))
