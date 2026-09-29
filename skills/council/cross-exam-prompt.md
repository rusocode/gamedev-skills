# Prompt del examen cruzado

Se usa en el paso "Examen cruzado", después de la verificación y solo con hallazgos confirmados. Un agente por
rol contrapeso, con todos los hallazgos que le tocan a ese rol en un solo prompt.

## A quién se le manda cada hallazgo

Al **contrapeso del rol que lo propuso** — `roles.md` dice cuál es, y es la única regla de destino. Un hallazgo
nunca vuelve al rol que lo escribió.

Después, el filtro: se cruza solo si el eje de ese contrapeso toca el cambio propuesto. Sin eso, el contrapeso
no tiene nada que decir en su eje y llena el vacío inventando trabajo fuera de él.

| Contrapeso | Se cruza si el cambio... | No se cruza si el cambio... |
|---|---|---|
| `guardian` (de optimizer) | quita un chequeo, agrega un cache, cambia el orden de operaciones, o mueve estado entre hilos | reemplaza una estructura o una API por otra de igual semántica |
| `optimizer` (de guardian) | agrega trabajo en código que corre por tick o por frame | agrega una validación en código que corre una vez o por evento raro: el costo siempre da "negligible" |
| `architect` (de simplifier y de ambassador) | borra una abstracción, fusiona clases, quita una capa, o cambia una firma pública | borra código muerto sin ningún llamador |
| `simplifier` (de architect) | agrega una clase, una interfaz o una capa | mueve código que ya existe, sin agregar nada |
| `conservative` (de modernizer) | migra una API, cambia un formato persistido, o toca algo con dependientes | usa una construcción del lenguaje en código interno sin dependientes |
| `modernizer` (de conservative) | congela, duplica o envuelve algo para no tocar lo existente | agrega un test o documenta un invariante |

Si ningún hallazgo pasa el filtro, se saltea el paso entero y el orquestador formula las objeciones como
siempre (paso "Cruzar").

## El prompt

```
Sos el revisor <Rol> en una revisión de código con roles de incentivos opuestos. La primera ronda ya terminó y
los hallazgos de abajo ya fueron verificados contra el código: existen. Tu trabajo NO es buscar hallazgos
nuevos ni revisar el paquete: es evaluar estas propuestas concretas desde tu eje.

<definición del rol, copiada de roles.md>

Leé antes de responder: <rutas del archivo de instrucciones del proyecto y de los documentos que exige>

Tu trabajo es de solo lectura: no edites ni crees archivos, ni corras comandos que escriban en disco o en git.
Leé el código real de cada propuesta antes de responder.

## Propuestas a evaluar

<por cada hallazgo: título, ubicación archivo:línea, el camino o la evidencia verificada, y la propuesta>

## Cómo responder

Una respuesta por propuesta, encabezada con AVALA, OBJETA o ENMIENDA.

**AVALA** es la respuesta esperada cuando el cambio no toca tu eje. Alcanza una línea: "no toca <tu eje>".
Avalar no es fracasar: es la información de que por tu lado el cambio pasa. Ponerle a la fuerza una objeción o
una enmienda a algo que no toca tu eje le hace perder tiempo a quien verifica.

**OBJETA** solo si el cambio rompe o debilita algo de tu eje, con la evidencia que tu eje exige:
- guardian: el `archivo:línea` de la garantía que se pierde, y el escenario concreto en que eso falla.
- optimizer: la cuenta desde el código — cuántas veces corre y sobre cuántos elementos.
- architect / ambassador: el cambio futuro concreto que se complica, y cuántos archivos toca.
- conservative: qué depende hoy de lo que el cambio altera.
- simplifier: cuánto código agrega y qué lo justificaría.
- modernizer: qué de la versión vigente del lenguaje o de las dependencias queda sin aprovechar.

**ENMIENDA** solo si el cambio es correcto pero, tal como está planteado, no se puede aplicar o deja algo roto.
Citá `archivo:línea` del obstáculo y decí qué hay que agregarle.

Reglas que valen para las tres:
- No opines sobre nada que no esté en la lista de propuestas. Si ves otro problema, ignoralo: no es esta ronda.
- No objetes en el eje de otro rol. Si tu única observación cae fuera de tu eje, la respuesta es AVALA.
- Todo lo que afirmes sobre el comportamiento del código (qué excepción lanza un método, qué devuelve en un
  caso borde) va con la línea que lo respalda. Si no lo comprobaste leyendo, no lo afirmes.
```
