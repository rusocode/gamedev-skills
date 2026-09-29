---
name: council
description: >
  Use when the user invokes /council to review a file or directory with reviewers of opposing incentives
  (simplifier, guardian, optimizer, architect, conservative, modernizer, ambassador).
argument-hint: <path> [role1, role2, ... | all]
disable-model-invocation: true
---

# Council

## Overview

Revisores con incentivos opuestos ven trade-offs que un revisor genérico no ve, pero cada uno infla su propio
terreno: sin verificación, los primeros puestos del informe terminan ocupados por hallazgos falsos. El trabajo
central de esta skill es verificar, no recolectar.

## Argumentos

`$ARGUMENTS` = `<path> [roles]`.

- Sin ruta: preguntala y pará.
- Roles: lista separada por comas, o `all`. Por defecto `simplifier, guardian, optimizer`.
- Las definiciones están en `roles.md`, en el mismo directorio que este archivo. Si piden un rol que no está
  ahí, listá los válidos y pará.
- `simplifier`, `guardian` y `optimizer` pasaron varias rondas de prueba contra código real; `architect`,
  `conservative`, `modernizer` y `ambassador` no. Marcalos como "sin probar" en el encabezado del informe si
  están en la lista, y también si el examen cruzado (paso 6) lanza a uno como contrapeso — con los roles por
  defecto, el contrapeso de `simplifier` es `architect`, así que puede pasar sin que el usuario lo pida.

## Proceso

1. **Preparar.**
    - Listá los archivos fuente de la ruta con sus líneas.
    - Si hay `CLAUDE.md`, `AGENTS.md` u otro archivo de instrucciones del proyecto en la raíz del repo, leelo y
      anotá su ruta y las de los documentos que exige leer antes de revisar o planificar (codemaps, ADRs). Al
      revisor le llegan esas rutas, no un resumen tuyo.
    - Si es repo git, guardá la salida de `git status --porcelain` como foto inicial.
2. **Lanzar.** Un `Agent` (`subagent_type: general-purpose`) por rol, todos en un mismo mensaje. El prompt es
   `reviewer-prompt.md` completado. Pasá rutas, no código pegado: el revisor tiene que poder buscar llamadores
   fuera del alcance.
3. **Esperar a todos.** Los pasos siguientes necesitan la respuesta de cada revisor. Si el entorno corre los
   agentes en segundo plano, seguí esperando sus notificaciones: el informe se escribe recién cuando volvió el
   último.
4. **Controlar efectos.** Si es repo git, compará `git status --porcelain` con la foto inicial. Todo cambio
   nuevo lo produjo un revisor: mostráselo al usuario antes de deshacerlo.
5. **Verificar cada hallazgo** leyendo vos el código. Antes de comprobar nada, escribí en una línea su **premisa
   central**: la afirmación sin la cual el hallazgo no existe, no un detalle de apoyo. Elegila por su carga, no
   por su literalidad — probá cada candidata con "si esto fuera falso, ¿el hallazgo muere?". "Se llama dos veces"
   es literal y fácil de confirmar; "ese segundo llamado repite trabajo" es la que sostiene el hallazgo, y es la
   que tenés que verificar. La nombrás vos, no el revisor: el que propone tiende a elegir la parte más fácil de
   defender. Y la nombrás **antes** de verificar,
   porque es lo único que corta la maniobra de después: cuando la premisa cae, retroceder a "bueno, en realidad
   lo importante era esta otra cosa, que sí se cumple". Verificá la premisa primero; si cae, el hallazgo termina
   ahí y no hace falta seguir con el resto.

   Después, eslabón por eslabón del "Camino" (no solo el primero y el último). Cada tipo de eslabón se comprueba
   así:
    - **Llamada:** la llamada existe en esa línea.
    - **Excepción:** la línea que la lanza corre en el mismo hilo que quien la recibiría (una tarea encolada falla
      en el hilo trabajador, no en quien la encola).
    - **Concurrencia:** escribí el orden de operaciones de cada hilo, incluidas las tareas que el mismo camino
      encola. Si una operación posterior de ese orden deja el estado bien, el intercalado no es un bug.
    - **Origen:** si el camino arranca en un dato o estado anómalo (archivo corrupto, valor fuera de rango,
      executor apagado), existe código que hoy lo produce. Si solo puede venir de afuera del programa (disco
      dañado, edición a mano), es origen externo y la severidad máxima es media.
    - **Frecuencia:** entre el disparador (tick, frame, evento) y el código no hay un return temprano, un cache
      o una condición que corte las ejecuciones.
    - **Consecuencia:** el dato o el estado afectado es el que el hallazgo dice.

   En un hallazgo de mantenimiento no hay camino que seguir: lo que se verifica es la Evidencia. Rehacé vos la
   búsqueda — para código muerto, buscá el nombre en todo el repo y también como string, porque reflexión,
   inyección de dependencias, JSON o configuración lo usan sin que aparezca como llamada; y mirá la visibilidad
   antes de dar por sobrante una clase o un método público.

   Asigná un estado. **Confirmado**: la premisa central se comprobó y ningún otro eslabón la contradice. **Refutado**:
   la premisa central no se cumple, es condicional ("si alguien modificara...", "aunque hoy no
   pasa") sin código actual que la produzca, o el comportamiento que el hallazgo quiere cambiar está puesto a
   propósito — lo dice un documento del proyecto, lo explica un javadoc, o hay un test que lo fija. **Dudoso**: la
   premisa se cumple pero un eslabón secundario depende de datos que solo se ven en ejecución.

   **Una premisa central refutada no se suaviza.** No baja a "dudoso", no baja de severidad, y no se reformula
   como un hallazgo más chico que sí sobreviva: va a Refutados. Si al verificarla notaste algo real alrededor,
   eso es un hallazgo nuevo, con su propia premisa y su propia verificación desde cero — no un rescate de este.

   Refutar exige la misma evidencia que confirmar: si un eslabón tiene varias ramas (un valor por defecto y uno
   presente, un caso vacío y uno lleno), la refutación tiene que cubrirlas todas.
    - Si el razonamiento es falso pero señala estado mutable o compartido real, seguí ese estado hasta quienes lo
      escriben y lo leen: ahí suele estar el bug que el revisor rodeó sin ver.
    - La severidad final la asignás vos con los criterios de `reviewer-prompt.md`; la del revisor no cuenta.
6. **Examen cruzado**, solo con los confirmados y solo con los que pasen el filtro de `cross-exam-prompt.md`
   (ese archivo dice a qué rol va cada hallazgo y cuándo vale la pena cruzarlo). Un agente por rol contrapeso,
   con todos los hallazgos que le tocan juntos en un prompt. Valen los pasos 2, 3 y 4 igual que en la ronda 1:
   mismo tipo de agente, esperá a que vuelvan todos, y volvé a comparar `git status --porcelain`. Verificá sus
   respuestas con las reglas del paso 5: una objeción o enmienda también puede apoyarse en una premisa falsa. Si
   ningún hallazgo pasa el filtro, saltealo.
7. **Cruzar.** Un mismo lugar señalado por dos roles sube de prioridad. Propuestas opuestas sobre el mismo
   código son un conflicto que decide el usuario. A los confirmados que no fueron al examen cruzado, partí del
   campo "Costo" que ya escribió el revisor y verificalo como cualquier otra afirmación; si no se sostiene o
   quedó vacío, formulá vos la objeción. Distinguí en el informe las que vinieron de un revisor real.
8. **Guardar el informe.** Escribilo en `council-report-<AAAA-MM-DD>.md`, en el directorio de trabajo, con la
   plantilla de abajo. Si ya existe uno con esa fecha, agregale `-2`, `-3`, etc. Así el informe sobrevive a que
   se compacte la conversación o se cierre la sesión.
9. **Informar** en el chat, en el idioma del usuario: el mismo contenido del archivo, más una primera línea con
   la ruta donde quedó guardado.

Plantilla:

```
## Council sobre <ruta> — <roles>

Revisores: <rol> (<n> hallazgos), <rol> (<n>), ...
<si algún rol de la lista es "sin probar": una línea avisándolo, con los nombres>

<1-3 líneas: lo más importante que dejó la verificación>

### Confirmados
1. **<título>** — `<archivo>:<línea>` — <roles> — <severidad>
   Premisa central: <la afirmación sin la cual el hallazgo no existe, y el archivo:línea que la sostiene>
   [defecto] Disparador: <archivo:línea del código que hoy produce el estado de partida>
   [defecto] Camino: <archivo:línea → archivo:línea → ... → consecuencia>
   [defecto] Estado final: <cómo queda el dato después de que corren todas las operaciones del camino, incluidas
   las encoladas>
   [mantenimiento] Evidencia: <qué comprobaste — las búsquedas que hiciste, el uso incorrecto que habilita, o el
   cambio futuro que se complica>
   Verificado: <qué archivo:línea leíste y qué comprobaste en cada punto>
   Propuesta: <cambio>
   Costo: <la respuesta del contrapeso — marcá si vino del examen cruzado (rol + AVALA/OBJETA/ENMIENDA, y si
   la verificaste) o si la formulaste vos>

### Dudosos
- **<título>** — `<archivo>:<línea>` — <qué dato de ejecución lo decidiría>

### Conflictos
- `<archivo>:<línea>`: <rol A> quiere <X>, <rol B> quiere <Y>. Recomendación: <...>

### Refutados (<n>)
- <título> (<rol>): <su premisa central, y qué muestra el código en su contra, con archivo:línea>
```

Cada hallazgo usa los campos de su forma: un **defecto** (algo se rompe o cuesta de más) lleva Disparador,
Camino y Estado final; uno de **mantenimiento** (código que sobra, un nombre que miente, un límite mal puesto)
lleva Evidencia en su lugar — ahí la ausencia de llamador no refuta nada, es el hallazgo mismo.

Entra en Confirmados solo si completás con código real los campos de su forma. Un defecto cuyo disparador es
"ninguno hoy" o cuyo estado final queda bien va a Refutados; si depende de datos de ejecución, a Dudosos.

Omití las secciones vacías. Cerrá ofreciendo aplicar, de a uno, los confirmados que el usuario elija.

## Errores comunes

| Error                                                  | Corrección                                                    |
|--------------------------------------------------------|---------------------------------------------------------------|
| Ordenar y deduplicar hallazgos y llamarlo verificación | Verificar es abrir el código citado y el llamador             |
| Heredar la severidad que puso el revisor               | Reclasificar con los criterios: sin camino real no hay alta   |
| Confirmar mirando solo el inicio y el final del camino | Comprobar cada eslabón; los falsos suelen romperse en medio   |
| Pegar el código en el prompt del revisor               | Pasar rutas, para que pueda buscar usos                       |
| Saltear el archivo de instrucciones del proyecto       | Sus decisiones documentadas refutan muchos falsos positivos   |
| Cruzar todos los confirmados contra todos los roles    | Solo los que pasan el filtro; el resto es ruido pago          |
| Dar por buena una objeción del examen cruzado sin leer | Una objeción también se apoya en premisas falsas              |
| Nombrar la premisa central después de verificar        | Primero se nombra, después se comprueba; si no, se retrofitea |
| Salvar un hallazgo con premisa refutada reformulándolo | Va a Refutados; lo que quede en pie es un hallazgo nuevo      |
