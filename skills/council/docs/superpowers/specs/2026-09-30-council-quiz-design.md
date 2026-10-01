# Diseño: cuestionario interactivo de la skill Council

## Propósito y público

Cuestionario de práctica individual para el usuario, que lo responderá personalmente para comprobar su comprensión de la skill Council.

## Diseño propuesto para revisión

- Interfaz y contenido en español.
- 10 preguntas de opción múltiple, con cuatro opciones seleccionables por pregunta.
- Cada pregunta aparece en su propia pantalla. El usuario avanza y puede volver a una pregunta anterior para cambiar su respuesta.
- Si el usuario selecciona una respuesta incorrecta, esa pantalla muestra de inmediato por qué la opción elegida es incorrecta, con una explicación basada en la skill. La retroalimentación aclara el concepto sin adelantar la letra u opción correcta.
- Al finalizar, se muestra el puntaje total sobre 10 y, para cada pregunta, la respuesta elegida, la respuesta correcta y una explicación breve.
- El contenido de cada pregunta y sus explicaciones se deriva de la skill Council real, en particular `SKILL.md` y el `README.md` accesibles en este repositorio.

## Cobertura del contenido

Las preguntas cubrirán hechos y distinciones expresas de la skill: el propósito de Council y la verificación de hallazgos; la preparación de la revisión; selección de roles y roles no probados; revisión independiente; verificación de la afirmación clave y de cada eslabón del recorrido; estados Confirmed, Refuted y Doubtful; contraexamen y su filtro; comparación de hallazgos; y formato y ubicación del informe.

Las respuestas correctas y las explicaciones se comprobarán contra la fuente antes de entregar el cuestionario. Los distractores serán plausibles, pero no tergiversarán la skill.

## Flujo

1. El usuario lee las instrucciones breves del cuestionario.
2. Responde una pregunta por pantalla, eligiendo una de cuatro opciones.
3. Si elige una opción incorrecta, recibe una explicación inmediata del error basada en la fuente.
4. Puede avanzar o volver a preguntas anteriores para revisar sus elecciones.
5. Al finalizar, recibe el puntaje y la corrección explicada de las 10 preguntas.

## Límites

- No se guardan respuestas ni puntajes entre sesiones.
- No se incluyen temporizador, aleatorización, inicio de sesión, telemetría ni conexión de red.
- El cuestionario no ejecuta ni simula una revisión Council: evalúa comprensión de la skill.

## Criterios de aceptación

- Hay exactamente 10 preguntas y exactamente cuatro opciones seleccionables por pregunta.
- Toda la experiencia está en español y cada pregunta ocupa una pantalla separada.
- El usuario puede elegir una respuesta, avanzar y volver a cambiarla antes de finalizar.
- Después de elegir una respuesta incorrecta, se explica inmediatamente por qué esa opción es incorrecta, sin revelar directamente cuál opción es la correcta.
- El resultado final muestra el puntaje sobre 10 y, para cada pregunta, la opción elegida, la correcta y una explicación basada en la fuente real.
