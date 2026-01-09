# DEMO — ServiBot

Resumen rápido
- ServiBot es un asistente multimodal con RAG sobre documentos, subida/indexado de ficheros, agente (planner→executor→evaluator), OCR, generación de PDFs/Excel y voz (STT/TTS).
- Estado actual: backend y frontend funcionando localmente; LM Studio corriendo en `http://127.0.0.1:1234`; voice (Whisper) y generación de archivos operativos.

URLs principales
- Backend API: http://127.0.0.1:8000
- Frontend UI: http://localhost:5173
- LM Studio API: http://127.0.0.1:1234

Arranque (rápido)
1. Backend:
   cd backend
   python -m uvicorn app.main:app --reload
2. Frontend:
   cd frontend
   npm run dev
3. LM Studio: asegurarse que está corriendo y el modelo cargado.

Endpoints útiles (ejemplos PowerShell)
- Health:
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -Method Get
- Voice status:
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/voice/status" -Method Get
- Generate PDF:
  POST http://127.0.0.1:8000/api/generate/pdf  (JSON body; use charset=utf-8)
- List generated files:
  GET http://127.0.0.1:8000/api/generate/list
- TTS synth:
  POST http://127.0.0.1:8000/api/voice/synthesize  (JSON body; use charset=utf-8)

Interfaz: flujo y pruebas (cómo usarla)
1. Subida e indexado
   - Arrastra o selecciona archivos (TXT, PDF, imágenes).
   - Estados: Uploading → Indexing → Indexed (o Error).
   - Si aparece X, usar reintentar o revisar `/api/upload/status/{file_id}`.

2. Chat con RAG
   - Escribe o graba (botón 🎤) y envía.
   - Respuesta incluye resumen y chips de fuentes (clickables).
   - "Ver más" aparece si hay >6 fuentes.

3. Voice Input (Whisper local)
   - Pulsar botón micrófono, grabar, detener.
   - Transcripción automática al input; enviar para procesar.

4. Voice Output (gTTS/pyttsx3)
   - Tras respuesta del asistente, pulsar "🔊 Escuchar respuesta".
   - Reproductor integrado con play/pause, velocidad, volumen, descarga.

5. Gestor de archivos (FileManager)
   - Modal con lista, checkboxes, descargar, eliminar, limpiar todo (confirmación).

6. Exportar conversación
   - Botón Exportar → PDF o Excel.
   - PDF: formateado con títulos/párrafos.
   - Excel: hojas Conversación / Estadísticas / Timeline del agente.

Comandos de prueba concretos (PowerShell, use charset utf-8)
- Generar PDF (ejemplo):
  $body = '{"title":"Reporte","content":"Contenido\n\nMás texto","filename":"demo.pdf"}'
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/generate/pdf" -Method Post -Body $body -ContentType "application/json; charset=utf-8"
- Generar TTS (ejemplo):
  $ttsBody = '{"text":"Hola, soy ServiBot","language":"es","engine":"gtts"}'
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/voice/synthesize" -Method Post -Body $ttsBody -ContentType "application/json; charset=utf-8"

Comprobaciones en disco (rutas)
- Uploads: `backend/data/uploads/`
- Generated files: `backend/data/generated/`
- Audio: `backend/data/audio/`
- Upload status/persistencia: `backend/data/upload_status.json`

Problemas comunes y soluciones
- "There was an error parsing the body": en PowerShell usar JSON literal + `ContentType 'application/json; charset=utf-8'`.
- Librerías no encontradas en venv: usar `python -m pip install ...` desde la carpeta backend y verificar `sys.executable`.
- Chroma collection inexistente en clear: manejado con try/except en backend; ok.
- Si RAG responde "Plan ejecutado (simulación)": verificar que haya documentos indexados; comprobar `/api/debug/vectors`.

Checklist de pruebas
- [ ] Subir TXT/PDF/imagen → Indexed
- [ ] Preguntar por contenido → Respuesta con fuentes
- [ ] Click chip fuente → abre/descarga archivo
- [ ] Grabar voz → ver transcripción
- [ ] Reproducir TTS → audio funciona y descarga
- [ ] Exportar PDF/Excel → archivos generados y descargables
- [ ] Gestor: seleccionar y eliminar archivos
- [ ] Timeline del agente → ver pasos y tiempos

Script para demo (sugerido)
1. Presentación breve
2. Subida de documentos y ver indexado
3. Preguntar sobre contenido (RAG + fuentes)
4. Voice input demo (grabación + transcripción)
5. Voice output demo (reproducir TTS)
6. Exportar conversación (PDF/Excel)
7. Gestión de archivos (descargar/eliminar)
8. Cierre y próximos pasos

Siguientes pasos recomendados (sin APIs externas)
- Integrar VoiceRecorder/AudioPlayer/FileGenerator en frontend (si no está ya).
- Añadir tooltips con estado de indexación en chips.
- Mejorar prompts y few-shot para LM Studio.
- Añadir pruebas E2E básicas (Playwright).

Notas finales
- LM Studio está operativo en `127.0.0.1:1234` con `Qwen2.5-7b-Instruct`.
- Se priorizó funcionalidad local (no integrar APIs externas hasta necesario).
- Para cualquier fallo, revisar logs del backend (uvicorn) y del LM Studio.
