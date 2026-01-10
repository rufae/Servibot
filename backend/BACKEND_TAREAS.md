# BACKEND - Estado y Tareas Pendientes

**Actualización:** 2026-01-09  
**Versión backend:** En desarrollo  
**Tests passing:** 42/46 agent tests (91.3%)

---

## ✅ CORRECCIONES APLICADAS (de BACKEND_ISSUES.md)

### Issue #1: POST /api/upload - Error parsing multipart ✅
- **Acción:** Agregado logging detallado de `filename` y `content_type`
- **Acción:** Agregada validación de `filename` no vacío
- **Archivo:** [app/api/upload.py](app/api/upload.py#L143-L151)
- **Estado:** ✅ Completado

### Issue #2: Endpoint streaming /api/chat/stream ✅
- **Acción:** Implementado endpoint SSE con eventos: `plan`, `step`, `response`, `done`, `error`
- **Archivo:** [app/api/chat.py](app/api/chat.py#L320-L420)
- **Features:** Streaming en tiempo real de pasos del agente
- **Estado:** ✅ Completado

### Issue #3: Estructura sources inconsistente ✅
- **Acción:** Ya estaba normalizado en líneas 234-244 de `chat.py`
- **Verificación:** Sources siempre devuelve `list[str]`
- **Estado:** ✅ Verificado OK

### Issue #4: CORS configuración ✅
- **Acción:** Verificado `CORS_ORIGINS` incluye localhost:3000 y 127.0.0.1:3000
- **Archivo:** [app/core/config.py](app/core/config.py#L48-L53)
- **Estado:** ✅ Completado

### Issue #5: Content-Disposition header ✅
- **Acción:** Agregado header `attachment` en GET `/api/upload/file/{file_id}`
- **Archivo:** [app/api/upload.py](app/api/upload.py#L326-L328)
- **Estado:** ✅ Completado

### Issue #6: Paginación en /api/upload/list ✅
- **Acción:** Implementada paginación con params `skip` y `limit` (default 50)
- **Archivo:** [app/api/upload.py](app/api/upload.py#L294-L329)
- **Features:** Ordenamiento por fecha (newest first), campo `has_more`
- **Estado:** ✅ Completado

### Issue #7: ChromaDB telemetry warnings ✅
- **Acción:** Desactivada telemetría con `anonymized_telemetry=False`
- **Archivo:** [app/db/chroma_client.py](app/db/chroma_client.py#L38-L42)
- **Estado:** ✅ Completado

---

## 🧪 ESTADO TESTS

### Tests Agent (backend/tests/test_agent/)
- **Total:** 46 tests
- **Passing:** 42 tests (91.3%)
- **Failing:** 4 tests
  - `test_email_intent` - Planner no detecta intent email
  - `test_calendar_intent` - Planner no detecta intent calendar
  - `test_ocr_intent` - Planner no detecta intent OCR
  - `test_multiple_intents` - Planner genera 2 subtasks en vez de 3+

**Desglose por módulo:**
- Evaluator: 12/12 ✅ (100%)
- Executor: 16/16 ✅ (100%)
- Planner: 14/18 ⚠️ (77.8%)

---

## 🔧 TAREAS PENDIENTES PARA BACKEND 100%

### Prioridad CRÍTICA (hacer AHORA) 🔴

#### 1. Mejorar detección de intents en Planner
- **Objetivo:** Detectar intents `email`, `calendar`, `ocr` en user messages
- **Acción:** Agregar reglas heurísticas en [app/agent/planner.py](app/agent/planner.py)
- **Ejemplos:** 
  - "Send an email" → tool `email`
  - "Schedule a meeting" → tool `calendar`
  - "Extract text from image" → tool `ocr`
- **Impacto:** 4 tests adicionales pasarán → 46/46 (100%)
- **Tiempo estimado:** 1h

#### 2. Implementar POST /agent/plan y /agent/execute
- **Objetivo:** Exponer planner y executor como endpoints REST independientes
- **Endpoints necesarios:**
  - `POST /api/agent/plan` → genera `ExecutionPlan` sin ejecutar
  - `POST /api/agent/execute` → ejecuta `ExecutionPlan` existente
  - `GET /api/agent/tools` → lista herramientas registradas
- **Archivo:** Crear `app/api/agent.py`
- **Tiempo estimado:** 2h

#### 3. Persistencia de ExecutionPlan y ExecutionResult
- **Objetivo:** Guardar planes y resultados en SQLite
- **Acciones:**
  - Crear modelo SQLAlchemy `ExecutionPlanModel` y `ExecutionResultModel`
  - Implementar CRUD en `app/db/execution_store.py`
  - Agregar migraciones con Alembic
- **Beneficio:** Historial completo de ejecuciones, retry mechanism
- **Tiempo estimado:** 3h

### Prioridad ALTA (hacer antes de demo) 🟠

#### 4. Webhook/callback para confirmaciones de usuario
- **Objetivo:** Permitir aprobar/declinar pasos que requieren `requires_user_confirmation=True`
- **Endpoints:**
  - `POST /api/agent/confirm/{plan_id}/{step}` → approve/decline
  - `GET /api/agent/pending/{plan_id}` → lista pasos pendientes
- **Integración:** Modificar `Executor` para pausar en confirmaciones
- **Tiempo estimado:** 2h

#### 5. Implementación real de herramientas externas
- **Email tool:** Integración con SendGrid/SMTP (1.5h)
- **Calendar tool:** Integración con Google Calendar API (1.5h)
- **OCR tool:** Integración con Tesseract o Google Vision (1.5h)
- **Notes tool:** Upgrade a Notion API (1.5h - opcional, mock funciona)
- **Tiempo estimado:** 6h total

#### 6. Endpoints de administración
- **Endpoints necesarios:**
  - `GET /api/admin/metrics` → métricas de sistema
  - `GET /api/admin/tools/{name}/status` → health check individual
  - `POST /api/admin/tools/{name}/restart` → reiniciar tool
  - `GET /api/admin/logs` → últimos logs
- **Archivo:** Crear `app/api/admin.py`
- **Tiempo estimado:** 2h

### Prioridad MEDIA (features avanzadas) 🟡

#### 7. Autenticación y autorización
- **Objetivo:** Proteger endpoints sensibles con JWT
- **Acciones:**
  - Endpoints: `/api/auth/login`, `/api/auth/register`, `/api/auth/me`
  - Middleware de autenticación
  - Roles: `user`, `admin`
- **Archivo:** Crear `app/auth/` module
- **Tiempo estimado:** 4h

#### 8. Retry policy y error handling
- **Objetivo:** Reintentar automáticamente herramientas fallidas
- **Acciones:**
  - Agregar `retry_count` y `retry_delay` a `SubTask` model
  - Implementar exponential backoff en `Executor`
  - Logging estructurado de errores
- **Tiempo estimado:** 2h

#### 9. Observabilidad y métricas
- **Objetivo:** Monitorear performance con Prometheus/OpenTelemetry
- **Métricas:** request_count, latency_histogram, error_rate
- **Tracing:** planner → executor → evaluator completo
- **Tiempo estimado:** 3h

#### 10. Tests end-to-end (E2E)
- **Objetivo:** Validar flujos completos usuario → backend → respuesta
- **Escenarios:**
  - Upload file → index → query → generate PDF
  - Multi-step agent execution con confirmaciones
  - Error recovery y retry
- **Archivo:** Crear `backend/tests/test_e2e/`
- **Tiempo estimado:** 4h

### Prioridad BAJA (nice-to-have) ⚪

#### 11. Documentación API con ejemplos (2h)
#### 12. Rate limiting y quotas (1h)
#### 13. Caching de queries RAG frecuentes con Redis (2h)

---

## 📊 RESUMEN TIEMPO ESTIMADO

| Prioridad | Tareas | Tiempo Total |
|-----------|--------|--------------|
| CRÍTICA 🔴 | 3 tareas | 6h |
| ALTA 🟠 | 3 tareas | 10h |
| MEDIA 🟡 | 4 tareas | 13h |
| BAJA ⚪ | 3 tareas | 5h |
| **TOTAL** | **13 tareas** | **34h** |

**Para backend 100% funcional:** ~16h (CRÍTICA + ALTA parcial)  
**Para backend production-ready:** ~34h (todas las tareas)

---

## 🎯 ROADMAP RECOMENDADO

### Semana actual (9-12 enero) - Sprint 1
- ✅ Corregir BACKEND_ISSUES (completado 9 enero)
- 🔄 Mejorar Planner intent detection (Tarea #1) - 1h
- 🔄 Implementar agent endpoints REST (Tarea #2) - 2h
- 🔄 Persistencia planes/resultados (Tarea #3) - 3h

### Semana 2 (13-19 enero) - Sprint 2
- Webhook confirmaciones (Tarea #4) - 2h
- Implementar email + calendar tools reales (Tarea #5 parcial) - 3h
- Endpoints admin (Tarea #6) - 2h
- Tests E2E básicos (Tarea #10 parcial) - 2h

### Semana 3 (20-26 enero) - Sprint 3
- Auth/JWT (Tarea #7) - 4h
- Retry policy (Tarea #8) - 2h
- Observabilidad básica (Tarea #9) - 3h
- Documentación API (Tarea #11) - 2h

### Semana 4 (27 enero - 2 febrero) - Sprint 4 (Opcional)
- OCR tool implementación real - 1.5h
- Rate limiting - 1h
- Caching Redis - 2h
- Tests E2E completos - 2h

---

## 🔍 VERIFICACIÓN RÁPIDA

Comandos para validar estado actual:

```bash
# Tests agent
pytest backend/tests/test_agent/ -v

# Health check
curl http://127.0.0.1:8000/api/health | jq

# Upload test
curl -X POST 'http://127.0.0.1:8000/api/upload' -F 'file=@test.txt'

# Chat test
curl -X POST 'http://127.0.0.1:8000/api/chat' \
  -H 'Content-Type: application/json' \
  -d '{"message":"¿Qué documentos tienes?"}' | jq

# Chat streaming test (SSE)
curl -N 'http://127.0.0.1:8000/api/chat/stream' \
  -H 'Content-Type: application/json' \
  -d '{"message":"Dame información sobre Laura"}'

# List files with pagination
curl 'http://127.0.0.1:8000/api/upload/list?skip=0&limit=10' | jq
```

---

## 📝 NOTAS IMPORTANTES

1. **Tests agent al 91.3%:** Solo faltan 4 tests relacionados con detección de intents. Solución rápida: mejorar heurísticas del Planner (1h).

2. **Endpoints críticos funcionando:** `/api/health`, `/api/chat`, `/api/upload`, `/api/chat/stream` ✅

3. **Streaming implementado:** Frontend puede conectar a `/api/chat/stream` para progreso en tiempo real ✅

4. **CORS configurado correctamente:** Frontend en localhost:3000 puede conectar sin issues ✅

5. **Telemetría ChromaDB desactivada:** No más warnings en logs ✅

6. **Pendiente crítico:** Implementar herramientas reales (actualmente mocks funcionan para desarrollo pero limitados).

7. **Falta persistencia:** ExecutionPlan/Results no se guardan en DB (se pierden al reiniciar).

---

*Documento actualizado automáticamente tras aplicar correcciones de BACKEND_ISSUES.md*
