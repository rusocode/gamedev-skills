---
name: drawing-pixel-art
description: Usar cuando haya que crear o retocar un sprite, icono, item o tile en pixel art (PNG de 16x16, 32x32, 64x64...) para un juego 2D, sin herramienta de dibujo a mano. Se activa ante "dibuja/crea un sprite", "haceme el pixel art de X", "genera la textura del item", "icono para el inventario", o cuando un sprite generado por codigo sale irreconocible, con bordes rotos o demasiado chico en el lienzo.
---

# Drawing Pixel Art

## Overview

El arte se **autora como una grilla de caracteres** (un caracter = un pixel = un color de la paleta) y un script la
convierte en PNG. El script es solo el pincel: la calidad sale de diseñar la silueta fila por fila, no de
primitivas de linea o rectangulo. Dibujar con `drawLine`/`fillRect` produce contornos en damero y formas que no se
leen.

## Cuando usar

- Sprite nuevo o rediseño para un juego pixel-perfect (`GL_NEAREST`, sin antialiasing).
- El resultado anterior salio irreconocible, con contorno discontinuo, o como un garabato de 10 px centrado.
- Hay que respetar el estilo de sprites existentes.

No usar para arte con antialiasing, gradientes o resoluciones > 64 px: ahi conviene una herramienta de dibujo.

Dibujar en la sesion principal, no delegar a un subagente: el que dibuja necesita mantener la imagen de la grilla
mientras escribe las filas y juzgar con honestidad el preview, y en pruebas solo Opus lo hizo bien (los modelos mas
chicos pasaban las validaciones con capsulas y bloques, o editaban `# huecos`/`# simetria` para que pasaran). Si
hay que delegar una tanda de sprites, pasar `model: opus` al agente.

## Receta

1. **Referencia.** Abrir 2-3 sprites vecinos con `Read` y anotar: tamaño del lienzo, color del contorno (casi
   nunca negro puro), cuantos tonos por material, direccion de la luz, cuanto del lienzo ocupan.
2. **Rasgos que identifican el objeto.** Antes de dibujar, listar 2-4 formas sin las cuales nadie lo reconoce y
   escribirlas como `# rasgo: ...` al inicio del mapa. Cada rasgo nombra una geometria comprobable en el mapa —
   un hueco, una curva, una linea de 1 px, dos brazos separados, un cambio de ancho — no un adjetivo ("solido",
   "forma de ancla"). Un anillo es un hueco rodeado de opaco; un arco es rama curva + cuerda recta + hueco entre
   ambas; unos brazos son dos piezas con transparencia entre medio. Declarar ademas lo que el script puede
   comprobar solo: `# huecos: N` (transparencia rodeada de opaco por los 4 lados: anillos, ojos, asas, el hueco
   entre grillete y cuerpo, el ojo de la cerradura) y `# espejo: x` (o `y`, `xy`) si el objeto es simetrico; el
   render **falla** hasta que la silueta cumpla las dos. Esas declaraciones son la especificacion: si fallan se
   corrigen las filas, no se borra la declaracion. El script devuelve los rasgos como checklist y el reporte final
   dice en que filas/columnas quedo cada uno. Una capsula, una media luna, un trapecio o un rectangulo con tonos no
   es un sprite.
3. **Silueta por filas, a mano.** Encuadre: el sprite ocupa al menos el 70% del lienzo en su lado mayor, con 1-2
   px de margen, centrado en el lienzo. Con `# espejo: x` se escribe **solo la mitad izquierda** (o superior con
   `y`) y el script completa la otra: la mitad de trabajo y simetria garantizada. El espejo solo rellena celdas
   transparentes de la mitad derecha, asi que para sombrear distinto cada lado se escriben esas celdas a mano y
   el resto se deja en `.`. Escribir la tabla de spans
   `fila -> col_inicio..col_fin` **fila por fila, con la forma real del objeto** (curvas, huecos, cambios de
   ancho). Para toda curva (cupula, bulbo, anillo, arco, escudo) copiar las filas de `references/shapes.md` en
   vez de inventarlas: los circulos ya estan rasterizados por diametro. No generar filas con helpers de
   centrado o padding: producen formas genericas. Proporciones reales:
   una pieza fina en el objeto es fina en el sprite (rama de arco u hoja de espada
   3-4 px, no 10); lo que en el objeto es una linea (cuerda, filo, cadena) es 1 px de color de contorno y separado
   por transparencia de la pieza vecina. Grosor minimo de una pieza con relleno: 3 px (contorno + relleno +
   contorno).
4. **Paleta.** Una letra por color, case-sensitive (`g` y `G` son distintos). Por material: claro / medio / oscuro,
   mas contorno `O` y brillo `w`. Alfa opcional para vidrio o agua.
5. **Escribir el mapa.** Archivo de texto: paleta, linea en blanco, filas (formato en la cabecera de `scripts/pixelmap.py`). El
   mapa tiene **exactamente** las dimensiones del lienzo pedido (32x32 = 32 filas de 32 caracteres), rellenando con
   el simbolo transparente: el PNG sale del tamaño del mapa.
6. **Contorno cerrado.** Regla: todo pixel opaco con un vecino (arriba/abajo/izq/der) transparente es contorno.
   No dibujarlo a mano: escribir la silueta solo con los tonos de relleno y renderizar con `--auto-outline`, que
   pinta de `O` cada pixel que toca transparencia (bordes, escalones, lineas de 1 px, huecos interiores). Sin
   `--auto-outline` el script falla listando cada fuga `(x,y)`; se arregla convirtiendo ese pixel a `O`, **nunca
   fusionando piezas separadas en un bloque** (el hueco entre rama y cuerda, entre anillo y vastago, es parte del
   dibujo).
7. **Sombreado.** Luz arriba-izquierda: brillo como franja vertical de 1-2 px a la izquierda, tono claro en el tercio
   superior, tono oscuro en una banda de 1-3 px pegada al contorno inferior y derecho. Detalles (burbujas, remaches,
   vetas) en 1-2 px del tono claro.
8. **Render + preview.**
   `python scripts/pixelmap.py render --map x.txt --out x.png --width 32 --height 32 --auto-outline --preview 8`, luego **leer
   `x_preview.png` con `Read`** y contrastarlo con la lista del paso 2: cada rasgo tiene que verse. A 1x no
   se ve nada; sin haber mirado el preview ampliado no hay verificacion, y el preview se entrega junto al PNG como
   evidencia.
9. **Iterar** sobre el mapa hasta que la silueta se lea a simple vista. Trabajar en scratchpad y **no pisar un asset
   del repo sin que lo pidan**. Cuando el usuario aprueba: el PNG va a la carpeta de texturas del juego y el mapa
   `.txt` se guarda en `examples/` de esta skill con el mismo nombre base, sumando su linea a la biblioteca de
   abajo — el mapa es la fuente y el PNG su compilacion, asi que un retoque futuro parte del mapa y no de cero, y
   el proximo objeto de silueta parecida parte de ese mapa. El preview no se guarda. Si el juego empaqueta atlas,
   recordar que hay que regenerarlo.

## Herramienta

`scripts/pixelmap.py` se invoca por su ruta absoluta con el interprete (`python <skill>/scripts/pixelmap.py ...`);
necesita Python 3 y Pillow (`pip install pillow`). `render` parsea el mapa, valida ancho, alto y
simbolos, pinta o valida el contorno, informa el bounding box, el % de lienzo ocupado, si toca el borde y cuantos
huecos cerrados hay (y donde), verifica `# huecos:` y `# simetria:` (falla si no se cumplen, pero deja el preview
para inspeccionar), devuelve la checklist de `# rasgo:`, guarda el PNG y un preview `NearestNeighbor` sobre fondo
verde. Leer toda esa salida: un "anillo" con `holes: 0` no es un anillo.

## Biblioteca de siluetas (`examples/`)

Antes de diseñar desde cero, buscar aca una silueta parecida y partir de ese mapa (cambiar paleta, proporciones
o detalles es mucho mas barato que inventar filas). Una linea por forma:

| Mapa               | Silueta                                                                                                     | Sirve de base para                                               |
|--------------------|-------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `potion.txt`       | bulbo redondo + cuello + corcho con liquido; contorno a mano, vidrio con alfa. Variantes: base roja, `azul` | toda pocion (nueva = otra `# variante`); frascos, jarras, bombas |
| `empty_bottle.txt` | la silueta de `potion` sin liquido: corcho + cuello + bulbo de vidrio translucido con reflejo               | la version vacia de cualquier pocion; viales, frascos, jarrones  |
| `bow.txt`          | arco fino en D + linea de 1 px + hueco; `--auto-outline`                                                    | arcos, hoces, lunas, asas, cuernos                               |
| `padlock.txt`      | arco sobre cuerpo rectangular con dos huecos; media silueta con `# espejo: x`                               | candados, bolsos, cofres con asa, campanas, faroles              |
| `helmet.txt`       | cupula (medio circulo D=24) + placa recta + 2 ranuras con puente + 2 orificios; `# espejo: x`, 4 huecos     | cascos, cubos, campanas invertidas, mascaras                     |

**Variantes de color.** Cuando dos sprites comparten la grilla y solo cambian tonos (pocion roja / azul / verde),
no se duplica el mapa: el mapa base declara `# variante nombre: sym=R,G,B[,A]; sym=...` por cada colorway y se
renderiza con `--variant nombre` (la base se renderiza sin `--variant`). Un sprite nuevo de esa familia es una
linea `# variante` mas, no un archivo mas. Si cambia la grilla, cambia para todas las variantes: ese es el
contrato; si un colorway necesita otra forma, entonces si es otro mapa.

`from-png` hace el camino inverso: reconstruye el mapa a partir de un PNG. Sirve cuando el usuario
retoca un sprite en un editor (Aseprite, Piskel): `python scripts/pixelmap.py from-png --png x.png --palette examples/x.txt
--out examples/x.txt` (con `--variant nombre` si el PNG es una variante) reutiliza los simbolos del mapa viejo, poda los
que ya no se usan, absorbe redondeos de ±2 por
canal, inventa simbolos solo para colores realmente nuevos, y se niega si hay mas de 8 (antialiasing o capas
semitransparentes: se arregla en el editor, no en el mapa). Las lineas `# rasgo/huecos/simetria` las **copia sin
revisar**: despues de reconstruir, renderizar el mapa nuevo — si `# huecos` o `# simetria` fallan, decidir con el
usuario si la edicion lo cambio a proposito (actualizar la declaracion) o fue un desliz — y releer los `# rasgo`
contra el preview, corrigiendolos si la forma cambio. Cerrar comparando pixel a pixel con el PNG: 0 diferencias
significa que el mapa vuelve a ser la fuente. Un PNG editado sin actualizar su mapa deja la biblioteca mintiendo.

Sin Python/Pillow a mano, el formato se renderiza con cualquier libreria raster con el mismo bucle de un pixel
por caracter; portar tambien las validaciones, que son lo que hace util al script.

## Errores comunes

| Sintoma                                          | Causa                                                    | Arreglo                                                                           |
|--------------------------------------------------|----------------------------------------------------------|-----------------------------------------------------------------------------------|
| Contorno en damero, forma "de alambre"           | Se dibujo con primitivas de linea                        | Rehacer como mapa de caracteres, silueta primero                                  |
| No se distingue que es                           | Piezas de 1-2 px, sin relleno ni tonos                   | Grosor >= 3 px por pieza, 3 tonos por material                                    |
| Un rasgo desaparecio (cuerda, mango)             | Solapa con otra pieza del mismo color, o nunca se dibujo | Separar 1 px o cambiar a color de contorno; ubicar cada `# rasgo` en el mapa      |
| Media luna gorda en vez de arco                  | Rama de 10 px sin cuerda                                 | Rama de 3-4 px, cuerda de 1 px recta, hueco transparente entre ambas              |
| Pixel de relleno tocando el fondo                | Escalon sin contorno al cambiar de ancho                 | `--auto-outline`, o convertir ese pixel a `O` (el script lo lista)                |
| Todo fusionado en un bloque macizo               | Se "resolvieron" las fugas juntando las piezas           | Volver a separar las piezas; las fugas se arreglan con contorno, no con relleno   |
| "Verificado visualmente" pero esta mal           | Se miro el PNG a 1x                                      | Generar y leer el preview 8x                                                      |
| Sprite diminuto en el centro                     | No se planifico el encuadre                              | Tabla de spans que use el lienzo menos 1-2 px de margen; el script avisa bajo 70% |
| Capsula / rectangulo con tonos en vez del objeto | Filas generadas con un helper de centrado o padding      | Escribir las filas a mano siguiendo los rasgos del paso 2                         |
| PNG de 32x24 cuando se pidio 32x32               | El mapa tenia menos filas                                | Rellenar con filas transparentes; pasar `--width`/`--height`                      |

## Señales de alarma — parar y volver al mapa

- "Quito `# simetria`/`# huecos` porque a esta escala no se puede cumplir" o "subo `# huecos` de 1 a 4 para que
  pase" — la declaracion es el spec; se arreglan las filas. Huecos que no estaban en la lista de rasgos son
  agujeros accidentales: tapar el relleno, no cambiar el numero.
- "Fusiono las piezas para que no haya fugas de contorno" — las fugas se pintan de `O` (`--auto-outline`), nunca
  se rellenan.
- "Genero las filas con un helper que centra/rellena" — eso da capsulas y trapecios; las filas se escriben a mano.
- "Todas las caracteristicas se ven claramente" sin haber leido el preview 8x ni la salida del script — no hay
  verificacion.
- "El script paso, listo" — la validacion prueba huecos, simetria y contorno, no que se entienda que es. Releer
  el preview despues de cada render que pasa; un buzon con ranura pasa los mismos tests que un yelmo.
