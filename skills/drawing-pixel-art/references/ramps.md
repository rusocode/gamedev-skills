# Rampas por defecto (copiar valores, no inventarlos)

Rampas de material con el matiz corrido (paso 4): sombras frias, luces calidas, cada escalon con la luminancia
(`0.299 R + 0.587 G + 0.114 B`) que tendria sin corrimiento. Son las que usan los mapas de la biblioteca y el
valor por defecto cuando el proyecto no tiene paleta propia; si la tiene, manda la del proyecto. Todo sprite de
ese material usa los mismos valores, asi dos objetos de piedra, de hierro o de madera salen del mismo color.

| Simbolo | Piedra        | Hierro        | Uso                            |
|---------|---------------|---------------|--------------------------------|
| `O`     | 38,32,50      | 24,20,36      | contorno                       |
| `D`     | 52,52,78      | 48,49,76      | borde oscuro interior          |
| `d`     | 82,86,110     | 74,80,106     | cara en sombra                 |
| `n`     | 104,110,124   | 104,111,126   | sombra media                   |
| `m`     | 132,134,138   | 134,140,152   | tono medio (casi neutro)       |
| `l`     | 178,176,166   | 174,172,168   | cara iluminada                 |
| `L`     | 204,200,184   | 208,206,198   | luz, alrededor del brillo      |
| `w`     | 236,232,212   | 244,241,230   | brillo especular               |

Fuente: `stone.txt` (piedra) e `iron_shield.txt` (hierro). El hierro es un poco mas azul en los medios y mas
contrastado que la piedra; la diferencia entre los dos la hacen el contraste y el brillo, no el color.

- **Menos tonos que la rampa** (una pieza chica, un herraje): elegir los escalones que hagan falta, sin
  saltearse la direccion de la luz.
- **Un tono que no esta en la tabla** (una rampa de 6 escalones con otras luminancias, como las dovelas de
  `iron_door.txt`): interpolar en RGB entre los dos escalones vecinos segun su luminancia. Como la luminancia es
  lineal en RGB, el tono interpolado cae justo en la luminancia buscada.
- **En un mapa con varios materiales**, las letras siguen siendo las de la familia del material (`W V U T S R`,
  `I i g`...); lo que se copia son los valores.

## Madera

Por ser un material calido, la madera corre de marron rojizo en la sombra a dorado en la luz, en vez de ir de
azul a crema. Tiene mas escalones porque una tabla o un mango recorren mas luminancias que una cara de piedra: se
toman los que hagan falta, con la misma regla de interpolacion.

| Luminancia | RGB         | Matiz | Saturacion |
|------------|-------------|-------|------------|
| 29.5       | 48,22,20    | 4     | 58%        |
| 38.9       | 62,30,24    | 9     | 61%        |
| 55.8       | 84,46,32    | 16    | 62%        |
| 75.0       | 110,64,40   | 21    | 64%        |
| 95.7       | 136,84,50   | 24    | 63%        |
| 119.5      | 164,108,62  | 27    | 62%        |
| 140.8      | 186,130,78  | 29    | 58%        |
| 165.7      | 206,158,100 | 33    | 51%        |
| 202.7      | 232,200,140 | 39    | 40%        |
| 228.4      | 246,228,184 | 43    | 25%        |

**Varias maderas en un mismo sprite** (marco y hoja de una puerta, madera nueva y gastada): si las dos usaran la
misma rampa se fundirian. La secundaria usa la misma rampa desaturada hacia el gris de su propia luminancia, con un
factor `k` entre 0 y 1: cada canal pasa a `Y + k * (c - Y)`, donde `Y` es la luminancia, asi que el brillo no
cambia. En la biblioteca: la hoja de `wood_door.txt` usa `k = 1` y el marco `k = 0.8`; las hojas de
`iron_door.txt` son madera gastada, con `k = 0.35`.

Fuente: `wood_shield.txt`, `stone_sword.txt`, `wood_door.txt`, `iron_door.txt` y `bow.txt`, que ya la usan. Los
contornos de las piezas de madera no se tocaron: cada mapa conserva el suyo.
