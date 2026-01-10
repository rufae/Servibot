Título: ServiBot — Agente autónomo multimodal para gestión personal y automatizaciones
Concepto central:
ServiBot es un agente conversacional multimodal que ayuda a usuarios a gestionar tareas
personales y profesionales mediante lenguaje natural. Combina RAG (búsqueda semántica
sobre documentos del usuario), un bucle agente Plan→Execute→Evaluate y herramientas para
manipular recursos (calendario, correo, generación de documentos). El sistema prioriza la
privacidad (procesamiento local de documentos y vector DB local) y la demostración de
conceptos (POC robusto y reproducible localmente).
Problema que resuelve:
Usuarios y pequeñas organizaciones manejan información dispersa (PDFs, emails, notas).
ServiBot facilita acceder, resumir y automatizar acciones sobre esa información mediante
consultas en lenguaje natural y generación automatizada de documentos (informes,
resúmenes, exportaciones).
Objetivos generales:
Objetivos medibles (Criterios de aceptación):
Proporcionar un POC funcional que permita subir documentos, indexarlos y consultarlos
mediante RAG.
Implementar un planner que descompone instrucciones complejas en pasos ejecutables y
un executor controlado (con confirmaciones para acciones que alteren recursos).
Ofrecer capacidades multimodales básicas: ingestión de PDF (OCR cuando haga falta),
transcripción de audio y TTS para respuestas.
Soportar exportación automatizada de resultados a PDF/Excel mediante una herramienta
interna ( file_writer ).
1. El proyecto arranca localmente y funciona con las instrucciones de instalación del
README.md .
2. Endpoint /api/upload permite subir un PDF y el sistema indica el estado de ingestión
(pendiente/completada) con trazas de debug.
3. Endpoint /api/chat responde tanto con planes JSON (planner) como con respuestas
enriquecidas por RAG cuando hay documentos indexados.
4. La UI (React) permite enviar mensajes, subir archivos y descargar artefactos generados
(PDF/Excel).
5. Tests básicos ( pytest ) cubren los endpoints críticos /api/chat y /api/upload .
Alcance para la entrega inicial (MVP):
Viabilidad:
Backend: FastAPI con endpoints para chat, upload, generación y TTS (stubs/mocks para
servicios externos cuando proceda).
Vector DB: Chroma local (duckdb+parquet) para persistencia de embeddings.
Embeddings: sentence-transformers (modelo pequeño para POC) con carga segura en
CPU.
Frontend: React + Tailwind con interfaz de chat, subida y reproductor/descarga de audio y
archivos generados.
Técnica: el stack elegido (FastAPI, Chroma, sentence-transformers, React) permite un
POC reproducible en equipos personales. Se prioriza el uso de opciones locales (pyttsx3
como fallback para TTS, procesos por lotes para embeddings) para evitar dependencias
estrictas de API externas.