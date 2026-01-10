# FRONTEND_TAREAS

Resumen consolidado del estado actual del frontend de ServiBot, APIs necesarias, funcionalidades pendientes y checklist de tareas prioritarias.

---

## 1. Objetivo
Proveer un único documento conciso que sirva como checklist y guía para terminar el frontend hasta un estado de producción funcional.

---

## 2. Estado actual (qué hay ahora)
- Infraestructura:
  - Proyecto React con Vite, TailwindCSS, ESLint y Prettier.
  - `vite` configurado y `VITE_API_URL` en `.env.example`.
- Servicios centralizados:
  - `src/services/api.js` (cliente axios central con interceptores).
  - `src/services/index.js` (wrappers: `chatService`, `uploadService`, `voiceService`).
- Hooks reutilizables:
  - `src/hooks/useChat.js` (sendMessage, generateTTS, setMessages, isLoading, audioUrlForMessage).
  - `src/hooks/useFileUpload.js` (uploadFile, uploadMultipleFiles, reindexFile, pollIndexStatus, setUploadedFiles).
  - `src/hooks/useToast.js` (manejo de toasts múltiples con show/hide helpers).
- Stores (Zustand): `src/store/index.js` con `useChatStore`, `useUploadStore`, `useSettingsStore`.
- Componentes clave:
  - `src/components/ChatInterface.jsx`
  - `src/components/FileUpload.jsx`
  - `src/components/VoiceRecorder.jsx`
  - `src/components/AgentTimeline.jsx`
  - `src/components/MarkdownRenderer.jsx`
  - `src/components/ui/Feedback.jsx` (toasts, banners, spinner, empty states)
- Tests:
  - Vitest + Testing Library configurados.
  - Tests unitarios y de componentes creados y ejecutados; actualmente 57/57 tests pasan.
- Deploy config: `vercel.json` y `.env.example` (usuario hará deploy manualmente).

---

## 3. Funcionalidades faltantes para llegar al 100%
(ordenadas por prioridad para entregar un MVP estable)

Prioritarias (imprescindibles):
- Conexión y validación completa contra el backend real (ajustar `VITE_API_URL`).
- Streaming en tiempo real para la `AgentTimeline` (WebSocket o SSE) — permite ver pasos del agente en vivo.
- FileManager completo: listado, preview, descarga, borrado, metadatos y paginación.
- Autenticación: login, refresh token, endpoints protegidos y manejo de sesión en cliente.
- Retries y fallback en `src/services/api.js` para llamadas críticas (exponible por configuración).
- Manejo robusto de errores de red y UX (toasts con acción: reintentar, ver detalles).

Importantes (UX y calidad):
- Mejora de accesibilidad (WCAG audit), focus management, contrastes, labels.
- Mejoras en la experiencia de voz: colas TTS, descarga de audio, controles persistentes.
- Integración RAG: UI para ver y abrir fuentes citadas por el asistente.
- Pruebas E2E (Playwright o Cypress) y tests de integración con MSW para endpoints.
- Observabilidad: captura de errores client-side y métricas (Sentry/analytics opcional).

Opcionales/avanzadas:
- Webhooks/callbacks para procesamientos largos.
- Panel admin para reindex masivo y monitoreo de vector DB.

---

## 4. APIs necesarias ahora (imprescindibles)
Formato resumido, payloads mínimos esperados:

- POST /api/chat
  - Request: { input: string, session_id?: string }
  - Response: { success: true, data: { response: string, sources?: [], plan?: [], generated_file?: { filename, download_url }, timestamp? } }

- POST /api/upload
  - Request: multipart/form-data file
  - Response: { success: true, data: { file_id, filename, download_url } }

- GET /api/upload/status/{file_id}
  - Response: { success: true, data: { status: 'indexing'|'indexed'|'error', progress?: number, attempts?: number } }

- POST /api/upload/reindex/{file_id}
  - Response: { success: true }

- POST /api/voice/transcribe
  - Request: audio file
  - Response: { success: true, data: { text } }

- POST /api/voice/synthesize
  - Request: { text, lang, engine? }
  - Response: { success: true, data: { audio_url } }

- GET /files/{file_id}/download (o `download_url` proporcionado por `/api/upload`)

---

## 5. APIs recomendadas para fases posteriores
- WebSocket o SSE: `/api/agent/stream` para emitir eventos/steps del agente.
- Auth: `POST /auth/login`, `POST /auth/refresh`, `GET /auth/me`.
- Search/Query: `POST /api/search` (consulta directa al vector DB) con parámetros de filtro.
- Admin: `POST /api/admin/reindex_all`, `DELETE /api/files/{id}`, etc.
- Analytics endpoint para eventos de uso.

---

## 6. Estado del frontend (qué falta, detallado)
- Integración backend real:
  - Confirmar formatos reales para `/api/chat` y `/api/upload`.
  - Probar con datos reales y ajustar parsing de `response`/`plan`.
- Streaming:
  - Implementar cliente WebSocket/SSE en `src/services/api.js`.
  - Consumir eventos y actualizar `useChatStore`/`AgentTimeline` en tiempo real.
- FileManager:
  - Componente de lista y modal/preview para cada archivo.
  - Paginación/filtrado y eliminación con confirmación.
- Auth:
  - Formularios y protección de rutas (almacenamiento seguro de tokens).
  - Middleware para añadir Authorization header en `api.js`.
- Tests y cobertura:
  - Aumentar cobertura de componentes (actualmente baja para varios componentes UI).
  - Añadir pruebas de integración MSW y E2E.
- UX y accesibilidad:
  - Revisión WCAG, keyboard flows, focus management, labels adicionales.
- Robustez:
  - Retries en `api.js`, timeouts y manejo de cancelación (AbortController).

---

## 7. Checklist Prioritario (tareas concretas y ordenadas)
1. Validar `VITE_API_URL` y probar `/api/chat` y `/api/upload` con el backend real.
2. Añadir retry/backoff en `src/services/api.js` para llamadas críticas.
3. Implementar WebSocket/SSE client en `src/services/api.js` y adaptar `AgentTimeline.jsx` para updates en tiempo real.
4. Crear `FileManager` (lista + preview + descarga + borrar) y rutas UI asociadas.
5. Implementar Auth (login + refresh token) y proteger endpoints UI.
6. Añadir pruebas MSW para endpoints y migrar algunos tests unitarios a pruebas de integración.
7. Añadir E2E básica (login → upload → chat flow) con Playwright/Cypress.
8. Auditar accesibilidad y corregir puntos críticos.
9. Pulir UI: empty states, loaders, manejo de errores visibles.
10. Preparar documentación de integración (ejemplos de payloads) en `frontend/README.md` o `FRONTEND_TAREAS.md`.

---

## 8. Comandos útiles
- Ejecutar tests (watch):
```bash
npm run test
```
- Ejecutar tests (CI):
```bash
npm run test:run
```
- Generar coverage:
```bash
npm run coverage
```
- Build producción:
```bash
npm run build
```
- Formatear:
```bash
npm run format
```
- Lint + autofix:
```bash
npm run lint:fix
```

---

## 9. Recomendaciones rápidas de implementación
- Para streaming: preferir SSE para compatibilidad sencilla desde backend (FastAPI supports SSE) o WebSocket si necesitas bidireccionalidad. Implementar reconexión progresiva y heartbeat.
- Para auth: usar cookies HttpOnly si el backend lo soporta; si usas tokens en localStorage, proteger con refresh token y manejo expiración.
- Tests: usar MSW (Mock Service Worker) para simular endpoints en pruebas de integración UI.
- Uploads: manejar AbortController para cancelar subidas largas y mostrar progreso con `onUploadProgress`.

---

## 10. Próximo paso que puedo ejecutar ahora
- Probar automáticamente los endpoints contra `VITE_API_URL` (smoke tests) y reportar diferencias de contract (necesita backend accesible desde tu máquina).
- Implementar cliente SSE/WebSocket base en `src/services/api.js` y ejemplo de uso en `AgentTimeline.jsx`.

Si quieres, empiezo por la tarea número 1 (validar `VITE_API_URL` y probar `/api/chat` y `/api/upload`)—dime si quieres que use mocks (MSW) o intentaré contactar tu backend real (asegúrate de que esté corriendo y de compartir la URL si es diferente a `http://localhost:8000`).

---

*Documento generado automáticamente por el asistente; puedes editarlo directamente si quieres prioridades distintas.*
