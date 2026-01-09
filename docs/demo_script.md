# Guion de Demo - ServiBot (5–7 minutos)

Objetivo: mostrar flujo clave del MVP: subir documento, hacer pregunta con RAG, pedir planificación y confirmar acción.

1. (0:00–0:30) Introducción rápida
   - Presentación: "Soy Rafa Castaño. Esto es ServiBot, agente autónomo multimodal." 
   - Objetivo de la demo: mostrar RAG y loop Plan→Execute→Evaluate en un escenario realista.

2. (0:30–1:30) Preparación
   - Mostrar la UI (chat + upload)
   - Explicar que el backend corre localmente (`http://localhost:8000`) y la UI en `http://localhost:3000`.

3. (1:30–2:30) Ingesta de documento
   - Subir un PDF de contrato/factura de ejemplo mediante el componente Upload.
   - Mostrar la respuesta del endpoint `/api/upload` y el mensaje "RAG ingestion pipeline will process it" (POC).

4. (2:30–4:00) Pregunta con contexto (RAG)
   - Enviar en chat: "¿Qué fecha figura en la cláusula 4 del contrato que acabo de subir?"
   - Mostrar cómo el agente consulta la base de conocimiento (POC) y devuelve una respuesta con referencia a la fuente (en la versión final esto será chunk+source).

5. (4:00–5:00) Planificación y ejecución controlada
   - Enviar en chat: "Organiza mi semana laboral y añade una cita el jueves a las 10"
   - Mostrar que el planner devuelve un plan JSON con subtareas, algunas requieren confirmación.
   - Confirmar la creación del evento (simular confirmación) y mostrar que el executor marca el paso como completado (mock execution).

6. (5:00–5:30) Cierre y puntos pendientes
   - Resumen: qué funciona ya, qué está en POC y próximos pasos (integraciones reales, persistencia de vector DB, TTS en la demo final).
   - Indicar que el repositorio contiene `README.md` con pasos para ejecutar localmente y `docs/concept.md` con objetivos.

Consejo para la grabación: mantener la pantalla limpia; pre-cargar el PDF de ejemplo; tener el terminal con uvicorn y el servidor de frontend visibles brevemente al inicio.
