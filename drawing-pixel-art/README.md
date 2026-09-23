# Guia de uso

Esta guia es para el **usuario**: que decir para que la skill haga lo que queres. El **como** se dibuja esta en
[`SKILL.md`](SKILL.md), que lo lee el agente.

La skill dibuja sprites como mapas de caracteres (un caracter = un pixel) y los compila a PNG
con [`scripts/pixelmap.py`](scripts/pixelmap.py), que ademas valida contorno, huecos, simetria, encuadre y relieve.
Las siluetas ya resueltas viven en [`examples/`](examples/) y las plantillas de curvas (circulos por diametro) en
[`references/shapes.md`](references/shapes.md).

## Instalacion

Cloná esta carpeta donde tu agente busque skills (`~/.claude/skills/`, `~/.agents/skills/`, o el directorio que
corresponda). Necesitas Python 3 con Pillow (`pip install pillow`).

## Ejemplos tipicos de uso

| Que queres                                                   | Prompt                                  |
|--------------------------------------------------------------|-----------------------------------------|
| Un sprite nuevo                                              | `Crea el sprite de una antorcha, 32x32` |
| Arreglar uno existente                                       | `Arregla el sprite ruta/X.png`          |
| Un cambio concreto en uno existente                          | `Sacale la piedrita a ruta/stone.png`   |
| Otro color del mismo sprite                                  | `Agrega una variante verde a la pocion` |
| Devolverle la fuente al mapa despues de editar el PNG a mano | `Edite a mano X.png, actualiza su mapa` |

Detalles que valen la pena:

- **Deci "sprite", "textura", "item" o "icono"** en algun lado: es lo que activa la skill.
- **No digas "retoca" ni "redibuja"**. Esos son el *resultado* del diagnostico, no la orden — pedir
  "retoca" sobre un sprite pintado de 200 colores es imposible y la instruccion se contradice sola.
- **El tamaño no hace falta** si el sprite ya existe: sale del archivo.

## Que decide la skill y que decidis vos?

Antes de tocar un sprite existente, la skill corre `pixelmap.py audit --png X.png`, que **mide** el
archivo y dicta la tecnica:

- **RETOUCH** — es pixel art autorado: se reabre el PNG como mapa, se corrige ahi, y todo lo que no se
  toca queda identico pixel a pixel.
- **REDRAW** — esta pintado con pincel suave o reducido de una imagen grande, asi que los pixeles hay
  que recolocarlos a mano.

Eso es lo unico que la medicion resuelve. Cuando da REDRAW queda **una** pregunta, que es tuya:

> ¿se conserva la silueta o no?

- **Se conserva** → el original sirve de plano: misma forma y composicion, pixeles y sombreado nuevos.
- **No se conserva** → rediseño: la forma se dibuja de cero.

Si no lo aclaras, la skill pregunta antes de dibujar la primera fila. Lo podes adelantar con media
linea: `..., conservando la silueta` o `..., la silueta podes cambiarla si no se lee`.

## Cuando conviene explicar el motivo?

No hace falta justificar lo que la auditoria ya mide: colores de mas, falta de contorno, sprite plano,
encuadre chico. Si hace falta cuando el problema es el **dibujo**, porque eso no lo mide nadie:

- "no se entiende que es"
- "la silueta esta mal, no la uses de referencia"
- "la pose es rara"
- "las monedas parecen galletitas"

## Que pasa despues

1. Todo el trabajo sale en una carpeta de borradores fuera de los assets reales (`sandbox/` del
   proyecto si existe, si no el scratchpad del entorno).
2. Te llega el PNG con un **preview ampliado 8x** — a 1x no se juzga nada.
3. **Nada entra al repo hasta que aprobes.** Recien ahi el PNG va a la carpeta de texturas y el mapa
   `.txt` a `examples/`, que es la biblioteca de siluetas de la que parten los sprites siguientes.

Corregir el PNG vos mismo en un editor es parte del flujo, no una excepcion: se reimporta con
`from-png` y el mapa vuelve a ser la fuente.
