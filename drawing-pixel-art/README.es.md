<div align="center">

# Drawing Pixel Art

**Skill especialista en dibujar y arreglar sprites en Pixel Art.**

![Python 3](https://img.shields.io/badge/python-3.x-3776AB?logo=python&logoColor=white)
![Pillow](https://img.shields.io/badge/deps-Pillow-8CAAE6)
![Sprites](https://img.shields.io/badge/sprites-16%E2%80%9364%20px-2E7D32)

<img src="example.png" width="560">

<sub>Ejemplo real utilizando el prompt **<i>"Arreglá el item wood_shield.png"</i>**.</sub>

🌐 [English](README.md) | **Español**

</div>

---

## Contenido

- ⚙️ [Cómo funciona](#cómo-funciona)
- 📦 [Instalación](#instalación)
- 🧠 [Qué modelo conviene](#qué-modelo-conviene)
- 💬 [Cómo pedirle cosas](#cómo-pedirle-cosas)
- 🎛️ [Qué decide la skill y qué decidís vos](#qué-decide-la-skill-y-qué-decidís-vos)
- 📝 [Cuándo conviene explicar el motivo](#cuándo-conviene-explicar-el-motivo)
- ✅ [Qué pasa después](#qué-pasa-después)
- 🗂️ [Estructura](#estructura)

## ⚙️ Cómo funciona

Los sprites se escriben como **mapas de caracteres** (un carácter = un píxel = un color de la paleta) y se compilan
a PNG con [`scripts/pixelmap.py`](scripts/pixelmap.py):

```
mapa .txt  ──►  pixelmap.py render  ──►  PNG + preview 8x
                      │
                      └─ valida contorno, huecos, simetría, encuadre y relieve
```

Las siluetas ya aprobadas viven en [`examples/`](examples/) y las plantillas de curvas (círculos por diámetro) en
[`references/shapes.md`](references/shapes.md).

## 📦 Instalación

Copiá la carpeta `drawing-pixel-art/` donde tu agente busque skills (`~/.claude/skills/`, `~/.agents/skills/` o
el directorio que corresponda):

```bash
git clone https://github.com/rusocode/ruso-skills.git
cp -r ruso-skills/drawing-pixel-art ~/.claude/skills/
```

**Requisitos:** Python 3 y Pillow.

```bash
pip install pillow
```

## 🧠 Qué modelo conviene

El dibujo lo tiene que hacer el modelo más fuerte que tengas a mano, con el razonamiento extendido activo; en la
práctica, **Opus**. No es una preferencia: `pixelmap.py` valida contorno, huecos, simetría, encuadre y que el
sprite no sea plano, pero **no valida que el dibujo sea bueno**. Un sprite puede pasar el audit entero y aun así
tener el reborde en 3 tonos, ninguna textura y un degradado que no sigue el volumen.

Medido sobre el mismo encargo (arreglar un `wood_shield.png` de 32x32, conservando la silueta en ambos casos):

|                              |  Sonnet   |            Opus            |
|------------------------------|:---------:|:--------------------------:|
| Veredicto del audit          |   pasa    |            pasa            |
| Silueta                      | D=28, 88% |    D=28, 88% (idéntica)    |
| Tonos de relleno / dominante | 11 / 26%  |          14 / 15%          |
| Reborde perimetral           |  3 tonos  | 7 tonos (bisel por normal) |
| Remaches / vetas             |   0 / 0   |           8 / 8            |

Los dos entregan un escudo redondo reconocible y los dos pasan todas las validaciones. La diferencia está entera en
el paso 7 (relieve y textura), que es justo lo que ningún script puede medir por vos.

> [!TIP]
> Si el sprite sale correcto pero soso, revisá con qué modelo lo pediste antes de tocar el mapa.

## 💬 Cómo pedirle cosas

| Qué querés                                                   | Prompt                                  |
|--------------------------------------------------------------|-----------------------------------------|
| Un sprite nuevo                                              | `Creá el sprite de una antorcha, 32x32` |
| Arreglar uno existente                                       | `Arreglá el sprite ruta/X.png`          |
| Un cambio concreto en uno existente                          | `Sacale la piedrita a ruta/stone.png`   |
| Otro color del mismo sprite                                  | `Agregá una variante verde a la poción` |
| Devolverle la fuente al mapa después de editar el PNG a mano | `Edité a mano X.png, actualizá su mapa` |

Detalles que vale la pena tener en cuenta:

- **Decí "sprite", "textura", "item" o "icono"** en algún lado: es lo que activa la skill.
- **No digas "retocá" ni "redibujá".** Eso es el *resultado* del diagnóstico, no la orden. Pedir "retocá" sobre
  un sprite pintado de 200 colores es imposible y la instrucción se contradice sola.
- **El tamaño no hace falta** si el sprite ya existe: sale del archivo.

## 🎛️ Qué decide la skill y qué decidís vos

Antes de tocar un sprite existente, la skill corre `pixelmap.py audit --png X.png`, que **mide** el archivo y
dicta la técnica:

| Veredicto   | Diagnóstico                                                    | Qué se hace                                                                                       |
|-------------|----------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **RETOUCH** | Es pixel art autorado.                                         | Se reabre el PNG como mapa y se corrige ahí. Todo lo que no se toca queda idéntico píxel a píxel. |
| **REDRAW**  | Está pintado con pincel suave o reducido de una imagen grande. | Los píxeles hay que recolocarlos a mano.                                                          |

Eso es lo único que la medición resuelve. Cuando da REDRAW queda **una** pregunta, y es tuya:

> **¿Se conserva la silueta o no?**
>
> - **Se conserva** → el original sirve de plano: misma forma y composición, píxeles y sombreado nuevos.
> - **No se conserva** → rediseño: la forma se dibuja de cero.

Si no lo aclarás, la skill pregunta antes de dibujar la primera fila. Lo podés adelantar con media línea:
`…, conservando la silueta` o `…, la silueta podés cambiarla si no se lee`.

## 📝 Cuándo conviene explicar el motivo

No hace falta justificar lo que la auditoría ya mide: colores de más, falta de contorno, sprite plano, encuadre
chico. Sí hace falta cuando el problema es el **dibujo**, porque eso no lo mide nadie:

- *"no se entiende qué es"*
- *"la silueta está mal, no la uses de referencia"*
- *"la pose es rara"*
- *"las monedas parecen galletitas"*

## ✅ Qué pasa después

1. Todo el trabajo sale en una carpeta de borradores fuera de los assets reales (`sandbox/` del proyecto si existe;
   si no, el scratchpad del entorno).
2. Te llega el PNG con un **preview ampliado 8x**: a 1x no se juzga nada.
3. **Nada entra al repo hasta que lo apruebes.** Recién ahí el PNG va a la carpeta de texturas y el mapa `.txt` a
   `examples/`, que es la biblioteca de siluetas de la que parten los sprites siguientes.

> [!NOTE]
> Corregir el PNG vos mismo en un editor es parte del flujo, no una excepción: se reimporta con `from-png` y el mapa
> vuelve a ser la fuente.

## 🗂️ Estructura

| Ruta                                           | Qué es                                                            |
|------------------------------------------------|-------------------------------------------------------------------|
| [`SKILL.md`](SKILL.md)                         | Instrucciones para el agente: el proceso de dibujo paso a paso.   |
| [`scripts/pixelmap.py`](scripts/pixelmap.py)   | CLI con `render` (mapa → PNG), `from-png` (PNG → mapa) y `audit`. |
| [`scripts/bands.py`](scripts/bands.py)         | Ayudas para rebordes de ancho constante y bisel según la luz.     |
| [`examples/`](examples/)                       | Mapas aprobados: la biblioteca de siluetas.                       |
| [`references/shapes.md`](references/shapes.md) | Plantillas de curvas (círculos por diámetro).                     |
