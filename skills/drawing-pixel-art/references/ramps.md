# Rampas compartidas (copiar valores, no inventarlos)

Rampas de material con el matiz corrido (paso 4): sombras frias, luces calidas, cada escalon con la luminancia
(`0.299 R + 0.587 G + 0.114 B`) que tendria sin corrimiento. Todo sprite que tenga ese material usa estos valores,
asi dos objetos de piedra o de hierro salen del mismo color.

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

La madera todavia no tiene rampa compartida: cada mapa usa la suya (`wood_door.txt`, `wood_shield.txt`,
`stone_sword.txt`).
