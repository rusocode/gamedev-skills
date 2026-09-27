---
name: drawing-pixel-art
description: Usar cuando haya que crear o retocar un sprite, icono, item o tile en pixel art (PNG de 16x16, 32x32, 64x64...) para un juego 2D, sin herramienta de dibujo a mano. Se activa ante "dibuja/crea un sprite", "haceme el pixel art de X", "genera la textura del item", "icono para el inventario", o cuando un sprite generado por codigo sale irreconocible, con bordes rotos, demasiado chico en el lienzo, o plano (caras de un solo tono, sin relieve).
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

Dibujar con el modelo mas fuerte disponible y el razonamiento extendido activo (en pruebas, **Opus**), en la
sesion principal y no delegado a un subagente: el que dibuja necesita mantener la imagen de la grilla mientras
escribe las filas y juzgar con honestidad el preview. Si hay que delegar una tanda de sprites, pasar
`model: opus` al agente.

Hay dos modos de falla distintos con modelos mas chicos, y el segundo es el peligroso:

- **Rompen el contrato**: capsulas y bloques en vez de la forma, o editan `# huecos`/`# simetria` para que las
  validaciones pasen. Se ve enseguida en la salida del script.
- **Cumplen el contrato y se quedan cortos en el paso 7.** Medido sobre el mismo encargo (`wood_shield.png`,
  32x32, misma silueta D=28 de `references/shapes.md`, ambos con `audit` en verde y 0 colores usados una sola
  vez): reborde perimetral de 3 tonos contra 7, tono dominante 26% contra 15%, cero remaches y cero vetas contra
  ocho de cada uno. Ninguna validacion atrapa eso — el `PLANO:` salta recien al 40% de dominante, asi que un
  sprite correcto pero soso pasa entero. La unica red es releer el preview 8x contra las listas de los pasos 2
  y 7, una por una.

## Receta

0. **Diagnostico (solo si el sprite ya existe).** `python scripts/pixelmap.py audit --png x.png` mide colores,
   colores usados una sola vez, tonos de relleno, tono dominante, luminancia del borde y encuadre, y dice que modo
   corresponde: **RETOUCH** (es pixel art autorado: se reabre con `from-png`, se corrige en el mapa y lo que no se
   toca queda identico pixel a pixel) o **REDRAW** (esta pintado o reducido de una imagen grande, `from-png` no
   puede con el; ahi hay que preguntar si la silueta se conserva o se rehace). Correrlo **antes** de decidir el
   modo: el estado del archivo es un dato medible, no una preferencia.
1. **Referencia.** Abrir 2-3 sprites vecinos con `Read` y anotar: tamaño del lienzo, color del contorno (casi
   nunca negro puro), cuantos tonos por material, direccion de la luz, cuanto del lienzo ocupan. **Antes de copiar
   un estilo, comprobar que ese vecino sea pixel art autorado**: contar sus colores y cuantos aparecen en un solo
   pixel. Decenas o cientos de colores, muchos de ellos unicos, y pixeles de borde claros en vez de contorno =
   imagen pintada con pincel suave o reducida de una grande, no un sprite dibujado pixel a pixel; sirve para saber
   **que** objeto es, no **como** dibujarlo. En una carpeta a medio migrar conviven los dos estilos, asi que la
   referencia sale de los vecinos que cumplen el paso 7 o de `assets/`, no del archivo mas cercano.
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
3. **Silueta por filas, a mano.** Encuadre: el sprite ocupa al menos el 70% del lienzo en su lado mayor, con al
   menos 1 px de margen en ese lado, centrado en el lienzo. El margen maximo lo pone el 70% (en 32x32, hasta 4 px
   por lado): dentro de ese rango se elige el que mejor quede. El lado corto sigue las proporciones del objeto, asi
   que su hueco no es margen de sobra (una pocion es angosta). Excepcion: lo que llena su casilla por diseño — una
   puerta, un tile, un fondo — llega al borde a proposito y lo declara con `# sangra: si`, que apaga el aviso de
   margen (ver `iron_door.txt`). Con `# espejo: x` se escribe **solo la mitad izquierda** (o superior con
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
4. **Paleta.** Una letra por color, case-sensitive (`g` y `G` son distintos). Presupuesto **por material, no por
   sprite**: la rampa de un material tiene tantos tonos como bandas de lugar tenga la pieza mas grande de ese
   material — un cilindro de 7 px visibles admite 7 bandas y ninguna mas, una cara de corte de 7x7 con anillo
   admite 5. En 32x32 eso da 5-7 tonos por material. Con un solo material sirve el esqueleto `D d n m l L`
   (de oscuro a claro, ver `stone.txt` y `gold.txt`); con varios **cada rampa lleva su propia familia de letras**,
   porque dos rampas no pueden compartir simbolo: en `iron_door.txt` la piedra es `W V U T S R`, la madera
   `n m k j h` y el hierro `I i g`. Elegir letras que recuerden al material y mantener el orden claro→oscuro dentro
   de cada familia. Mas el brillo `w` y el contorno `O`. El total sale solo: un material ~8 simbolos, dos ~14, cuatro ~
    22. **No hay tope fijo**; el limite es que dos
        tonos de la misma rampa se distingan a simple vista (si no se distinguen no son un escalon, son ruido) y un
        techo blando de ~32 simbolos. Medido en un atado de leña de 32x32 con cuatro materiales, renderizando el mismo
        dibujo con tres paletas: de 13 a 18 simbolos se nota, de 18 a 22 tambien (una banda por fila en vez de dither),
        y de 22 en adelante las piezas se quedan sin filas donde ponerlos. El estilo es **limpio**:
        tonos planos elegidos a mano, sin antialiasing ni ruido; el relieve sale de donde se pone cada tono (paso 7), no
        de
        la cantidad. Alfa opcional para vidrio o agua.
5. **Escribir el mapa.** Archivo de texto: paleta, linea en blanco, filas (formato en la cabecera de
   `scripts/pixelmap.py`). El
   mapa tiene **exactamente** las dimensiones del lienzo pedido (32x32 = 32 filas de 32 caracteres), rellenando con
   el simbolo transparente: el PNG sale del tamaño del mapa.
6. **Contorno cerrado.** Regla: todo pixel opaco con un vecino (arriba/abajo/izq/der) transparente es contorno.
   No dibujarlo a mano: escribir la silueta solo con los tonos de relleno y renderizar con `--auto-outline`, que
   pinta de `O` cada pixel que toca transparencia (bordes, escalones, lineas de 1 px, huecos interiores). Sin
   `--auto-outline` el script falla listando cada fuga `(x,y)`; se arregla convirtiendo ese pixel a `O`, **nunca
   fusionando piezas separadas en un bloque** (el hueco entre rama y cuerda, entre anillo y vastago, es parte del
   dibujo). La unica linea de `O` que se escribe a mano es la que separa dos piezas que se tocan sin transparencia
   entre medio (troncos apilados, monedas solapadas): `--auto-outline` no la ve, y sin ella las piezas se funden.
7. **Relieve.** Una silueta correcta con caras de un solo tono pasa todas las validaciones de forma y se ve plana.
   El relieve se declara en el mapa como lineas `# relieve: ...` (una por tecnica, con la posicion), igual que los
   rasgos, y el script las devuelve como checklist. Un sprite de 24 px o mas lleva **todas** estas:
    - **Rampa recorrida entera**: todos los tonos de la rampa del material aparecen, escalonados de la cara iluminada
      (arriba-izquierda: `L l`) a la cara en sombra (abajo-derecha: `d D`), pasando por `n m`; ningun tono cubre mas
      del 40% del relleno.
    - **Brillo especular**: mancha de `w` de 2-3 px rodeada de `L`, en el punto mas cercano a la luz de cada pieza (no
      una raya vertical de borde a borde).
    - **Borde oscuro interior**: 1 px de `D` pegado al contorno en el lado inferior y derecho de cada pieza.
    - **Dither medido**: 1 px de pixeles alternados en una frontera de tonos que en el preview se ve como escalon
      duro sobre una superficie curva o rugosa; nunca sobre el contorno ni en franjas de mas de 2 px. Entre dos
      tonos casi iguales no se percibe y no cuenta como relieve: mejor un escalon de rampa mas.
    - **Textura de superficie**, al menos una por pieza segun el material: hoyuelo (1 px `D` arriba-izquierda +
      1 px `l` abajo-derecha, para metal o piedra), veta o grieta de 1 px en `D` (madera, roca), cara hundida (arco de
      sombra `n` arriba-izquierda y arco de luz `l` abajo-derecha, para monedas, botones, remaches),
      reflejo vertical de `L` (vidrio, cristal).
      Detalles (burbujas, remaches, vetas) en 1-2 px, con contraste contra la cara donde estan.
8. **Render + preview.**
   `python scripts/pixelmap.py render --map x.txt --out x.png --width 32 --height 32 --auto-outline --preview 8`, luego
   **leer
   `x_preview.png` con `Read`** y contrastarlo con las listas de los pasos 2 y 7: cada rasgo y cada relieve tiene
   que verse. El script mide los tonos del relleno y **falla con `PLANO:`** si hay menos de 6 o uno cubre mas del
   40%; eso se arregla en el mapa con las tecnicas del paso 7, nunca declarando menos o achicando el sprite. A 1x no
   se ve nada; sin haber mirado el preview ampliado no hay verificacion, y el preview se entrega junto al PNG como
   evidencia.
9. **Iterar** sobre el mapa hasta que la silueta se lea a simple vista. Trabajar en un lugar temporal fuera de los
   assets reales — la carpeta `sandbox/` del proyecto si existe y esta en `.gitignore`, si no el scratchpad del
   entorno — y **no pisar un asset del repo sin que lo pidan**. Cuando el usuario aprueba: el PNG va a la carpeta de
   texturas del juego y el mapa
   `.txt` se guarda en `assets/` de esta skill con el mismo nombre base, sumando su linea a la biblioteca de
   abajo — el mapa es la fuente y el PNG su compilacion, asi que un retoque futuro parte del mapa y no de cero, y
   el proximo objeto de silueta parecida parte de ese mapa. El preview no se guarda. Si el juego empaqueta atlas,
   recordar que hay que regenerarlo.

## Herramienta

`scripts/pixelmap.py` se invoca por su ruta absoluta con el interprete (`python <skill>/scripts/pixelmap.py ...`);
necesita Python 3 y Pillow (`pip install pillow`). `audit` mide un PNG existente y dicta retocar o redibujar (ver paso
0). `render` parsea el mapa, valida ancho, alto y
simbolos, pinta o valida el contorno, informa el bounding box, el % de lienzo ocupado, si toca el borde y cuantos
huecos cerrados hay (y donde), verifica `# huecos:` y `# simetria:` (falla si no se cumplen, pero deja el preview
para inspeccionar), cuenta los tonos del relleno y el % del dominante (falla con `PLANO:` bajo 6 tonos o sobre 40%,
y si un sprite de 24 px o mas no declara `# relieve:`), devuelve las checklists de `# rasgo:` y `# relieve:`, guarda
el PNG y un preview `NearestNeighbor` sobre fondo verde. Leer toda esa salida: un "anillo" con `holes: 0` no es un
anillo, y `fill tones: 4` es un sprite plano aunque la silueta sea perfecta.

`scripts/bands.py` es opcional y solo sirve para objetos con **reborde perimetral** (escudos, monedas, puertas,
placas). No dibuja: `bands(spans, w, h)` convierte una tabla de spans escrita a mano en capas concentricas (1 =
contorno, 2..k = reborde, k+1 = ranura, resto = campo), y `bevel_index()` da el tono de cada pixel de reborde
segun cuanto mira su normal hacia la luz. Resuelve las dos cosas que salen mal a ojo: un reborde de ancho constante
(seguir el contorno a mano lo adelgaza en las diagonales) y un bisel que se lee como levantado en vez de como una
banda plana. El campo, el sombreado y los detalles siguen escribiendose a mano encima — ahi esta el dibujo, y un
reborde perfecto alrededor de una forma generica sigue siendo una capsula. Ejemplo completo en
`assets/iron_shield.txt`.

## Biblioteca de siluetas (`assets/`)

Antes de diseñar desde cero, buscar aca una silueta parecida y partir de ese mapa (cambiar paleta, proporciones
o detalles es mucho mas barato que inventar filas). Todos cumplen el paso 7, asi que tambien sirven de referencia
de sombreado, no solo de silueta. Una linea por forma:

| Mapa               | Silueta                                                                                                                                                                                                                                                                                                                                                   | Sirve de base para                                                                                                                    |
|--------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `potion.txt`       | bulbo redondo + cuello + corcho; vidrio con alfa y reflejo, liquido en rampa p R q r con dither. Variantes: base roja, `azul`                                                                                                                                                                                                                             | toda pocion (nueva = otra `# variante`); frascos, jarras, bombas                                                                      |
| `empty_bottle.txt` | la silueta de `potion` sin liquido: corcho + cuello + bulbo de vidrio translucido con rampa l/g/G, dither y dos reflejos                                                                                                                                                                                                                                  | la version vacia de cualquier pocion; viales, frascos, jarrones                                                                       |
| `bow.txt`          | arco fino en D + linea de 1 px + hueco; la rampa se recorre a lo largo del arco, no a lo ancho (una rama de 4 px solo deja 2 px de relleno). `--auto-outline`                                                                                                                                                                                             | arcos, hoces, lunas, asas, cuernos                                                                                                    |
| `padlock.txt`      | arco sobre cuerpo rectangular con dos huecos; media silueta con `# espejo: x`, luz cenital en bandas y brillo en el eje, que es el unico sombreado compatible con el espejo                                                                                                                                                                               | candados, bolsos, cofres con asa, campanas, faroles                                                                                   |
| `helmet.txt`       | cupula (medio circulo D=24) + placa recta + 2 ranuras con puente + 2 orificios, 4 huecos; ancho completo escrito a mano con luz diagonal y `# simetria: x`                                                                                                                                                                                                | cascos, cubos, campanas invertidas, mascaras                                                                                          |
| `stone.txt`        | roca poligonal (meseta, 45 grados, flancos verticales, base plana) con 3 caras, rampa completa, especular, dither, grietas y hoyuelo; `--auto-outline`                                                                                                                                                                                                    | rocas, minerales, carbon, lingotes toscos, bloques de tierra o hielo                                                                  |
| `iron_door.txt`    | arco de medio punto de dovelas con juntas de mortero sobre jambas rectas, doble hoja de madera y dos herrajes: tres materiales, tres rampas (6+5+3)                                                                                                                                                                                                       | puertas, portones, ventanas con arco, arcadas, muros de piedra, cofres con herrajes                                                   |
| `gold.txt`         | seis monedas de frente (circulos D=12/10/8) solapadas con contorno de 1 px a mano entre ellas; canto claro/oscuro, especular, cara hundida, emblema 2x2                                                                                                                                                                                                   | pilas de monedas, botones, fichas, escudos redondos, engranajes                                                                       |
| `chicken.txt`      | cuerpo redondeado de costado + muslo ovalado delante con anillo de contorno a mano + dos huesos de 2 px de relleno con punta de dos nudos; piel en rampa D d n m l L, hueso B b c                                                                                                                                                                         | comida asada (pollo, pierna, jamon), carnes, animales de costado, piezas con hueso                                                    |
| `wood_door.txt`    | marco recto de viga (dintel sobre dos postes) + hoja de tablas con juntas D, dos travesaños, tornapunta en Z con pendiente 2:1, bisagras de fleje y aldaba de anillo; tres rampas (hoja 7, marco 7, hierro 4)                                                                                                                                             | puertas y portones de madera, cajas, barriles de frente, empalizadas, carteles de tablas                                              |
| `iron_shield.txt`  | heater (dos arcos de circulo convergiendo en punta) con reborde perimetral de 3 px separado del campo por una ranura, nervadura vertical central con ranuras a los lados, 8 remaches en hoyuelo; rampa unica de metal (7 tonos)                                                                                                                           | escudos, blasones, placas de metal, cualquier heater liso o con relieve central                                                       |
| `wood_shield.txt`  | disco D=28 con reborde metalico perimetral de 3 px separado del campo por una ranura, cuatro tablas verticales con junta de 1 px y canto propio (cada tabla es un cilindro), umbo circular D=10 con anillo de contorno a mano, 8 remaches; dos rampas (madera 7, hierro 6)                                                                                | escudos redondos, ruedas, tapas de barril, blasones circulares, cualquier disco de tablas con herraje perimetral                      |
| `key.txt`          | vastago recto a 45 grados (banda diagonal c+r de 27 a 35, 9 px de ancho por fila) entre un anillo D=16 con ojo D=6 y dos dientes finos de 3 px que cuelgan perpendiculares, cada uno con rampa propia para no fundirse con la banda oscura del vastago; ojo hundido con arco de sombra arriba-izquierda y arco de luz abajo-derecha                       | llaves, objetos alargados en diagonal, anillos con vastago, piezas finas perpendiculares a un eje inclinado, agujeros pasantes        |
| `stone_sword.txt`  | espada diagonal de dos materiales sobre el eje c-r=0: hoja de piedra de 9 px de ancho por fila con punta de biseles simetricos y filo astillado (mellas y salientes de 1 px sobre c-r=+-4), guarda de madera perpendicular (banda c+r=38..42) y mango entre dos lineas de contorno rematado en un pomo de piedra D=5; dos rampas (piedra 6 + w, madera 6) | espadas, dagas, hachas, picos y cualquier herramienta en diagonal; piezas perpendiculares a un eje inclinado; filos de piedra tallada |

**Variantes de color.** Cuando dos sprites comparten la grilla y solo cambian tonos (pocion roja / azul / verde),
no se duplica el mapa: el mapa base declara `# variante nombre: sym=R,G,B[,A]; sym=...` por cada colorway y se
renderiza con `--variant nombre` (la base se renderiza sin `--variant`). Un sprite nuevo de esa familia es una
linea `# variante` mas, no un archivo mas. Si cambia la grilla, cambia para todas las variantes: ese es el
contrato; si un colorway necesita otra forma, entonces si es otro mapa.

`from-png` hace el camino inverso: reconstruye el mapa a partir de un PNG. Sirve cuando el usuario
retoca un sprite en un editor (Aseprite, Piskel): `python scripts/pixelmap.py from-png --png x.png --palette assets/x.txt
--out assets/x.txt` (con `--variant nombre` si el PNG es una variante) reutiliza los simbolos del mapa viejo, poda los
que ya no se usan, absorbe redondeos de ±2 por
canal, inventa simbolos solo para colores realmente nuevos, y se niega si hay mas de 32 (antialiasing o capas
semitransparentes: se arregla en el editor, no en el mapa). Las lineas `# rasgo/huecos/simetria` las **copia sin
revisar**: despues de reconstruir, renderizar el mapa nuevo — si `# huecos` o `# simetria` fallan, decidir con el
usuario si la edicion lo cambio a proposito (actualizar la declaracion) o fue un desliz — y releer los `# rasgo`
contra el preview, corrigiendolos si la forma cambio. Cerrar comparando pixel a pixel con el PNG: 0 diferencias
significa que el mapa vuelve a ser la fuente. Un PNG editado sin actualizar su mapa deja la biblioteca mintiendo.

Sin Python/Pillow a mano, el formato se renderiza con cualquier libreria raster con el mismo bucle de un pixel
por caracter; portar tambien las validaciones, que son lo que hace util al script.

## Errores comunes

| Sintoma                                               | Causa                                                    | Arreglo                                                                           |
|-------------------------------------------------------|----------------------------------------------------------|-----------------------------------------------------------------------------------|
| Contorno en damero, forma "de alambre"                | Se dibujo con primitivas de linea                        | Rehacer como mapa de caracteres, silueta primero                                  |
| No se distingue que es                                | Piezas de 1-2 px, sin relleno ni tonos                   | Grosor >= 3 px por pieza, rampa de 5-7 tonos por material                         |
| Se ve plano, "de plastico", aunque la forma este bien | Caras de un solo tono, brillo en raya, sin textura       | Paso 7 completo: rampa entera, especular en mancha, borde oscuro, dither, textura |
| `PLANO:` en el render                                 | Menos de 6 tonos o uno cubre mas del 40% del relleno     | Agregar escalones de rampa y textura en el mapa; no achicar ni declarar menos     |
| Un rasgo desaparecio (cuerda, mango)                  | Solapa con otra pieza del mismo color, o nunca se dibujo | Separar 1 px o cambiar a color de contorno; ubicar cada `# rasgo` en el mapa      |
| Media luna gorda en vez de arco                       | Rama de 10 px sin cuerda                                 | Rama de 3-4 px, cuerda de 1 px recta, hueco transparente entre ambas              |
| Pixel de relleno tocando el fondo                     | Escalon sin contorno al cambiar de ancho                 | `--auto-outline`, o convertir ese pixel a `O` (el script lo lista)                |
| Todo fusionado en un bloque macizo                    | Se "resolvieron" las fugas juntando las piezas           | Volver a separar las piezas; las fugas se arreglan con contorno, no con relleno   |
| "Verificado visualmente" pero esta mal                | Se miro el PNG a 1x                                      | Generar y leer el preview 8x                                                      |
| Sprite diminuto en el centro                          | No se planifico el encuadre                              | Tabla de spans con >= 1 px de margen en el lado mayor; el script avisa bajo 70%   |
| Capsula / rectangulo con tonos en vez del objeto      | Filas generadas con un helper de centrado o padding      | Escribir las filas a mano siguiendo los rasgos del paso 2                         |
| PNG de 32x24 cuando se pidio 32x32                    | El mapa tenia menos filas                                | Rellenar con filas transparentes; pasar `--width`/`--height`                      |

## Señales de alarma — parar y volver al mapa

- "Me pidieron el sprite nombrando el archivo que reemplaza, asi que copiarlo al repo ya esta autorizado" — no.
  "Crea X que reemplace Y.png" es **el encargo**, no la aprobacion. El PNG y su mapa se entregan en la carpeta de
  borradores con el preview y ahi se para, hasta que el usuario apruebe en un mensaje posterior. Lo mismo vale para
  sumar el mapa a `assets/`.
- `audit` dice **REDRAW** y me pongo a dibujar sin preguntar si la silueta se conserva — la auditoria decide la
  tecnica (si los pixeles se reaprovechan o hay que recolocarlos), **no** si el objeto puede cambiar de forma. Eso
  es del usuario: redibujar conservando la silueta usa el original como plano; rediseñar lo descarta. Preguntar
  antes de la primera fila, no despues del preview.
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
- "Con 3 tonos alcanza, es pixel art" o "mas detalle seria mas colores y el estilo es limpio" — el detalle es
  estructura (rampa recorrida, especular, borde oscuro, textura), no cantidad de colores; el oro paso de plano a
  con relieve con los mismos 8 simbolos. Un `PLANO:` se resuelve en el mapa, no bajando `FLAT_MIN_TONES`.
