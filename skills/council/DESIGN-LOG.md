# Historial de diseño de `/council`

No lo lee el agente que ejecuta la skill (no está referenciado desde `SKILL.md`). Es registro para quien la
edite después: qué falló en cada corrida de prueba y qué regla lo corrige. Sirve para no reintroducir un fallo
ya visto y para juzgar si una mejora nueva vale lo que cuesta.

## Metodología

`superpowers:writing-skills` (RED sin skill → GREEN con skill → REFACTOR repetido). 9 corridas de subagente
sobre dos paquetes Java reales (`world/chunk`, `io/chunk`), más 2 agentes de micro-test para el examen cruzado.
Una corrida completa (3 revisores + verificación + informe) promedió ~93k tokens, con un rango de 77k a 109k.

## Fallos observados y su corrección

| # | Fallo observado | Corrección aplicada |
|---|---|---|
| 1 | Sin skill: el orquestador ordenaba y deduplicaba hallazgos y lo llamaba "verificación"; los falsos quedaban arriba como CRÍTICO | Paso "Verificar": abrir el código citado, eslabón por eslabón del Camino |
| 2 | "Race condition" en `writeAll()` que no existía: el único llamador nunca reutiliza el mapa | Cada eslabón cita código real, no un llamador hipotético |
| 3 | Cifras inventadas ("cientos de MB", "-10% GC") sin ninguna cuenta | `reviewer-prompt.md`: cifras solo si se calculan desde el código, mostrando la cuenta |
| 4 | "Carga 100 veces por segundo" ignorando el `return` temprano de `Overworld.java:134` | Eslabón "Frecuencia": comprobar returns tempranos y caches entre el disparador y el código |
| 5 | "Si `onEvict()`/`writeChunks()` lanzan..." cuando esas llamadas solo encolan una tarea: la excepción real ocurre en el hilo trabajador | Eslabón "Excepción": la línea que la lanza corre en el mismo hilo que la recibe |
| 6 | Severidad ALTA por un crash que solo pasa con el archivo de guardado corrupto o editado a mano (el juego nunca lo escribe así) | Eslabón "Origen": si el estado inicial solo viene de afuera del programa, la severidad máxima es media |
| 7 | Guardian descartó la concurrencia porque "todo corre en el hilo de tick", ignorando el hilo de escritura que vive en otro paquete | `roles.md`: guardian también busca objetos que cruzan a un hilo que vive fuera del alcance |
| 8 | El orquestador escribió el informe citando 3 revisores cuando solo había vuelto 1 | Paso "Esperar a todos"; el informe arranca con "Revisores: rol (n hallazgos), ..." |
| 9 | Refutó el bug real de `destroyedDecoratives` con una razón que cubre una sola rama (`Set.of()` en el caso vacío) e ignora la otra (`HashSet` vivo cuando el chunk sí tiene entrada) | "Refutar exige la misma evidencia que confirmar": si el eslabón tiene ramas, hay que cubrirlas todas |
| 10 | Confirmó como "media" algo que el propio revisor planteaba como hipotético ("si una lista se modificara... aunque hoy se pasan snapshots") | Un eslabón condicional sin código actual que lo produzca va a Refutados |
| 11 | Faltaba forzar la evidencia mínima de un confirmado | Plantilla: campos obligatorios "Disparador" y "Estado final" |
| 12 | Un subagente dejó un archivo vacío (`eldest)`) en el repo durante una revisión "de solo lectura" | Paso "Controlar efectos": comparar `git status --porcelain` antes y después |

## Nunca detectado en 9 corridas

El bug real de `ChunkChanges.buildRecord` (`world/chunk/ChunkChanges.java:235`): encola el `int[][]` y el
`HashSet` vivos sin copiarlos, así que si el jugador edita el mismo chunk mientras el hilo de escritura
serializa, hay una carrera. Guardian pasó cerca dos veces (fallos #7 y #9) sin llegar a él. No hay regla que lo
resuelva: es el límite de lo que un revisor ve en una sola lectura.

## Examen cruzado (paso 6): por qué es selectivo

Antes de implementarlo se corrió un micro-test de 2 agentes sobre hallazgos ya confirmados de las corridas
anteriores, comparando la objeción de un contrapeso real contra la que el orquestador se había formulado solo.
El resultado fue asimétrico:

| Cruce | Objeción autoformulada | Objeción del contrapeso real | Veredicto |
|---|---|---|---|
| Guardian evalúa "agrupar escrituras en `Overworld.unloadAll()`" (de optimizer) | "evento raro, el ahorro no justifica la complejidad" | `Overworld.java:381-396` mezcla limpieza en memoria con persistencia: saltear `onEvict()` para agrupar deja `mobsResolved` y `pendingMobRecords` sin limpiar, y el javadoc de 386-387 dice que sus entradas quedarían "huerfanas para siempre". La propuesta no se puede aplicar sin refactorizar antes | **Positivo**: obstáculo real y verificado que el orquestador no había visto |
| Optimizer evalúa "validar offsets en `RegionFileManager.java:141`" (de guardian) | "una comparación por entrada (negligible)" | "Costo: negligible (O(1))" — la misma conclusión. Además eligió ENMIENDA y pidió más validaciones (eje de guardian), afirmando que con `data.length < TABLE_BYTES` la línea 137 "crea un buffer mal formado" y se "leerá basura": falso, `ByteBuffer.wrap` lanza `IndexOutOfBoundsException` ahí mismo | **Negativo**: nada nuevo en su eje, deriva de rol y una premisa falsa |

La asimetría es estructural. "¿Qué rompe este cambio?" es el trabajo del guardian, así que critica bien. "¿Cuánto
cuesta esta validación?" casi siempre da "negligible", así que el optimizer no tiene nada real que decir en su
eje y llena el vacío con trabajo ajeno. De ahí las tres decisiones de diseño:

1. **Filtro previo** (tabla en `cross-exam-prompt.md`): se cruza solo si el eje del contrapeso toca el cambio.
   Validaciones en código que corre una vez, renombres y borrados de código muerto quedan excluidos.
2. **AVALA presentado como la respuesta esperada**, explícitamente no un fracaso. No se usó una prohibición
   ("no te salgas de tu rol") porque `writing-skills` documenta que las prohibiciones se negocian bajo incentivo
   contrario; una expectativa positiva no deja nada que negociar.
3. **Las respuestas del examen cruzado se verifican** con las mismas reglas que los hallazgos de la ronda 1. Sin
   eso, el reclamo falso sobre `ByteBuffer.wrap` habría entrado al informe.

Costo medido en el micro-test: 63k y 86k tokens por agente, porque cada uno lee las instrucciones del proyecto y
el código de cero. Por eso el paso es selectivo y va después de la verificación: cruzar todos los hallazgos
contra todos los roles habría llevado una corrida de ~93k a ~270k tokens.

## Revisión de coherencia y primera corrida con el paso 6

Una revisión de los cuatro archivos encontró seis problemas, corregidos todos:

1. **El examen cruzado podía devolverle un hallazgo a quien lo propuso.** La tabla decidía el destino por tipo de
   cambio, así que una propuesta de guardian que "cambia el orden de operaciones" volvía a guardian; y no cubría
   a conservative, modernizer ni ambassador. Ahora el destino es una sola regla — el contrapeso de `roles.md` — y
   la tabla es solo el filtro de eje, con una fila por cada uno de los seis contrapesos.
2. **Se lanzaba un rol sin probar sin avisar.** Con los roles por defecto, el contrapeso de `simplifier` es
   `architect`, que nunca se probó. El aviso de "sin probar" ahora cubre también los roles del paso 6.
3. **La plantilla refutaba todo hallazgo de código muerto.** Los campos Disparador y Estado final se diseñaron
   para defectos; un hallazgo de mantenimiento consiste justamente en que no hay llamador, así que leída al pie
   de la letra la regla "si el disparador es «ninguno hoy», va a Refutados" lo descartaba. Ahora hay dos formas:
   **defecto** (Disparador / Camino / Estado final) y **mantenimiento** (Evidencia), esta última con severidad
   máxima media y con reglas propias de verificación (rehacer la búsqueda, incluido el nombre como string; mirar
   la visibilidad).
4. **El paso 6 lanzaba agentes sin heredar las protecciones de la ronda 1**: ni esperar a todos (fallo #8), ni
   volver a comparar `git status` (el control del paso 4 corre antes de que existan esos agentes).
5. **La objeción del contrapeso se formulaba dos veces**: el revisor ya completa un campo "Costo" que el paso 7
   ignoraba. Ahora parte de ese campo y lo verifica.
6. **Una fila de "Errores comunes" no venía de ningún fallo observado** ("no guardar el informe"): eliminada.

La corrida de validación sobre `io/chunk` fue la mejor de las 11 y la primera con el paso 6 activo:

- El examen cruzado corrió, eligió bien el destino y los tres veredictos aparecieron: `architect` **AVALÓ** un
  cambio de firma, `guardian` **ENMENDÓ** el agrupado de escrituras citando la invariante documentada de
  `RegionWriteQueue` (el mismo obstáculo del micro-test, reproducido), y `optimizer` **OBJETÓ** la copia
  defensiva en `writeAll()` por costo O(n) sin riesgo actual.
- Esa última objeción importa: **es el hallazgo falso que el orquestador había confirmado como real en corridas
  anteriores** (fallo #10). El examen cruzado lo frenó por sí solo, sin intervención.
- Tres hallazgos quedaron afuera del filtro con el motivo anotado. Los tres de severidad baja se verificaron
  contra el código y son reales.
- Costo: **117k tokens**, o sea ~24k sobre el promedio sin paso 6, no los ~150k estimados — el filtro deja afuera
  la mitad de los hallazgos y los agentes de la ronda 2 leen mucho menos código que los de la ronda 1.

Dos detalles menores que se dejaron sin corregir por inocuos: el agente respondió en inglés (el prompt de prueba
hablaba de un usuario abstracto, no del usuario real), y clasificó dos hallazgos de costo como "mantenimiento"
en vez de defecto, completando igual campos que sostienen el hallazgo.

## Premisa central (paso 5): tomado del repo `consejo-7-sabios`

Una lectura del código de ese repo —no solo del README— mostró que **sí tiene verificación**, en
`consensus.py:543` (`verify_plan_claims`), conectada en `orchestrator.py:662`: un subagente Verifier adversarial
por tarea, con presupuesto de herramientas sin tope, que rehace los conteos y las afirmaciones de existencia. Su
pieza más fuerte es `_enforce_core_refutation()`: el modelo marca `is_core: true` en la afirmación que *es* la
justificación de la tarea, y después **código Python** —no el modelo— fuerza que una premisa central refutada
refute la tarea entera. El docstring documenta que eso arregla una falla de calibración del 2026-05-30, donde una
tarea con premisa refutada se suavizó a "weakened" y sobrevivió en el plan: el mismo fallo #10 de esta tabla.

De ahí se tomó el mecanismo de **premisa central**, adaptado a lo que un markdown puede hacer:

- La nombra el orquestador, no el revisor (igual que allá la marca el verificador, no el sabio: quien propone
  elige la parte más fácil de defender).
- Se nombra **antes** de verificar, que es lo único que corta el retrofit posterior ("en realidad lo importante
  era esta otra cosa, que sí se cumple").
- Una premisa refutada **no se suaviza**: no baja a dudoso, no baja de severidad y no se reformula como un
  hallazgo más chico. Lo que quede en pie es un hallazgo nuevo con su propia verificación.
- Sin equivalente al guard determinista: acá la regla depende igual de que el modelo la aplique. Lo más cerca es
  que "Premisa central" sea un campo obligatorio de la plantilla, así no completarlo se nota.

Corrida de validación sobre `world/chunk` (121k tokens), resultado **partido**:

- **Lo que mejoró:** 3 refutados de 5, contra 0 en todas las corridas anteriores. Refutó los dos hallazgos de
  guardian, uno de ellos exactamente de la clase del fallo #5 ("si falla la escritura en `onEvict`"), con el
  argumento correcto: encola asincrónicamente y la excepción solo sale en `flush()`.
- **Lo que no:** los dos confirmados son débiles. Uno propone mover el guard de `Zone.DUNGEON` fuera de
  `ChunkChanges`, contra una decisión documentada en `CLAUDE.md`, en dos javadoc y fijada por el test
  `destroyDecorative_dungeonZone_throws`. El otro eligió como premisa "se mapea dos veces sobre el mismo
  Optional" —literalmente cierto— cuando los dos `.map()` extraen campos distintos y no hay trabajo repetido: el
  mecanismo fallando por el otro lado, con una premisa elegida demasiado débil desde el principio en vez de
  retrofiteada después.

Dos correcciones aplicadas a partir de esa corrida, **las dos sin probar todavía**: elegir la premisa por su
carga y no por su literalidad (con el test "si esto fuera falso, ¿el hallazgo muere?"), y contar un javadoc que
explique el comportamiento o un test que lo fije como evidencia de que está puesto a propósito, al mismo nivel que
un documento del proyecto.

## Sin probar

- Los roles `conservative`, `modernizer` y `ambassador`: nunca se lanzaron. `architect` solo actuó una vez, como
  contrapeso en el examen cruzado, no como revisor de ronda 1. `SKILL.md` obliga a marcarlos como "sin probar" en
  el informe si alguien los usa.
- El guardado en `council-report-<fecha>.md` **en el directorio de trabajo**: la corrida de validación lo escribió
  en un directorio temporal para no dejar archivos en el repo del usuario. Conviene que el repo tenga
  `council-report-*.md` en su `.gitignore`.