# Diseño: cuestionario interactivo de la skill Council

## Propósito y público

Cuestionario de práctica individual para el usuario, que lo responderá personalmente para comprobar su comprensión de la skill Council.

## Diseño aprobado

- Interfaz y contenido en español.
- 10 preguntas de opción múltiple, con cuatro opciones seleccionables por pregunta.
- Las 10 preguntas aparecen en una sola pantalla.
- El usuario puede seleccionar una respuesta por pregunta y revisar/cambiar sus selecciones antes de finalizar.
- Al finalizar, se muestra el puntaje total sobre 10, la respuesta elegida, la respuesta correcta y una explicación breve para cada pregunta.
- El contenido de cada pregunta y su explicación debe derivarse de la skill Council real, en particular `SKILL.md` y el `README.md` accesibles en este repositorio.

## Cobertura del contenido

Las preguntas cubrirán hechos y distinciones expresas de la skill: el propósito de Council y la verificación de hallazgos; la preparación de la revisión; selección de roles y roles no probados; revisión independiente; verificación de la afirmación clave y de cada eslabón del recorrido; estados Confirmed, Refuted y Doubtful; contraexamen y su filtro; comparación de hallazgos; y formato y ubicación del informe.

Las respuestas correctas y las explicaciones se comprobarán contra la fuente antes de entregar el cuestionario. Los distractores serán plausibles, pero no tergiversarán la skill.

## Flujo

1. El usuario lee las instrucciones breves del cuestionario.
2. Responde las 10 preguntas en la misma pantalla, eligiendo una de cuatro opciones en cada una.
3. Al finalizar, recibe el puntaje y la corrección explicada de las 10 preguntas.

## Límites

- No se guardan respuestas ni puntajes entre sesiones.
- No se incluyen temporizador, aleatorización, inicio de sesión, telemetría ni conexión de red.
- El cuestionario no ejecuta ni simula una revisión Council: evalúa comprensión de la skill.

## Criterios de aceptación

- Hay exactamente 10 preguntas y exactamente cuatro opciones seleccionables por pregunta.
- Toda la experiencia está en español y presenta las 10 preguntas en una sola pantalla.
- El usuario puede elegir y cambiar una respuesta en cada pregunta antes de finalizar.
- El resultado final muestra el puntaje sobre 10 y, para cada pregunta, la opción elegida, la correcta y una explicación basada en la fuente real.
- La respuesta correcta no se revela antes de finalizar.
