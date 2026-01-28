"""
Agent Executor Module
Executes planned tasks using available tools.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
import re

from app.agent.planner import ExecutionPlan, SubTask
from app.core.config import settings

logger = logging.getLogger(__name__)


def sanitize_conversation_history(history: Any, max_messages: int = 5) -> List[Dict[str, str]]:
    """
    Sanitiza el historial de conversación para prevenir circular JSON y limitar tamaño.
    
    Args:
        history: Historial de conversación (puede ser None, list, o cualquier tipo)
        max_messages: Número máximo de mensajes a mantener
        
    Returns:
        Lista limpia de diccionarios con solo role y content
    """
    if not history:
        return []
    
    if not isinstance(history, list):
        logger.warning(f"Conversation history is not a list: {type(history)}")
        return []
    
    sanitized = []
    for msg in history[-max_messages:]:  # Solo últimos N mensajes
        try:
            if isinstance(msg, dict):
                # Solo mantener role y content, convertir a strings simples
                role = str(msg.get('role', 'user'))
                content = str(msg.get('content', ''))
                
                # Truncar contenido muy largo
                if len(content) > 1000:
                    content = content[:1000] + "..."
                
                sanitized.append({
                    "role": role,
                    "content": content
                })
        except Exception as e:
            logger.warning(f"Error sanitizing message: {e}")
            continue
    
    return sanitized


class ExecutionResult(BaseModel):
    """Result of executing a subtask."""
    step: int
    status: str  # success, failed, pending, skipped
    tool_used: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    execution_time_seconds: float = 0.0


class Executor:
    """
    Agent executor that runs planned tasks using available tools.
    """
    
    def __init__(self):
        """Initialize the executor with available tools."""
        self.tools = {}
        logger.info("Executor initialized")
        # Register mock tools automatically when configured
        if getattr(settings, "USE_MOCKS", False):
            try:
                from app.tools.mocks import calendar_mock, email_mock, notes_mock, file_writer_mock

                self.register_tool("calendar", calendar_mock.create_event)
                self.register_tool("email", email_mock.send_email)
                # Register a compatibility wrapper that accepts a single 'action' string
                # Executor routes tools by calling tool_func(subtask.action)
                self.register_tool("notes", lambda action: notes_mock.create_note_from_action(action))
                self.register_tool("file_writer", file_writer_mock.write_file)
                logger.info("Mock tools registered by Executor")
            except Exception as e:
                logger.warning(f"Failed to register mock tools: {e}")
    
    def register_tool(self, name: str, tool_func):
        """
        Register a tool function.
        
        Args:
            name: Tool identifier
            tool_func: Callable tool function
        """
        self.tools[name] = tool_func
        logger.info(f"Tool registered: {name}")
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        user_confirmations: Optional[Dict[int, bool]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete execution plan.
        
        Args:
            plan: ExecutionPlan to execute
            user_confirmations: Dict of step numbers to confirmation status
            context: Additional context including RAG results, user message, etc.
            
        Returns:
            Execution results including status and outputs
        """
        logger.info(f"Executing plan with {len(plan.subtasks)} subtasks")
        
        results = []
        user_confirmations = user_confirmations or {}
        self.execution_context = context or {}  # Store context for use in subtasks
        
        for subtask in plan.subtasks:
            # Check if confirmation is required and provided
            if subtask.requires_confirmation:
                if subtask.step not in user_confirmations:
                    results.append(ExecutionResult(
                        step=subtask.step,
                        status="pending",
                        tool_used=subtask.tool,
                        result=None,
                        error="Awaiting user confirmation"
                    ))
                    continue
                
                if not user_confirmations[subtask.step]:
                    results.append(ExecutionResult(
                        step=subtask.step,
                        status="skipped",
                        tool_used=subtask.tool,
                        result=None,
                        error="User declined confirmation"
                    ))
                    continue
            
            # Execute subtask
            result = await self._execute_subtask(subtask)
            results.append(result)
            
            # If this was a rag_query, store results in context for next subtasks
            if subtask.tool == "rag_query" and result.status == "success" and result.result:
                if isinstance(result.result, dict):
                    # Store RAG results in context
                    if "summary" in result.result:
                        self.execution_context["rag_summary"] = result.result["summary"]
                    if "sources" in result.result:
                        self.execution_context["rag_sources"] = result.result["sources"]
                    logger.info(f"📦 Stored RAG results in context for downstream tasks")
            
            # Stop execution if critical step failed
            result_status = result.get('status') if isinstance(result, dict) else getattr(result, 'status', None)
            if result_status == "failed" and subtask.step in [1, 2]:
                logger.error(f"Critical step {subtask.step} failed, stopping execution")
                break
        
        # Count results properly (handle both dict and object)
        def get_status(r):
            return r.get('status') if isinstance(r, dict) else getattr(r, 'status', None)
        
        def serialize_result(r):
            """Serialize result to dict, handling both Pydantic models and dicts"""
            if isinstance(r, dict):
                return r
            elif hasattr(r, 'model_dump'):
                return r.model_dump()
            elif hasattr(r, 'dict'):
                return r.dict()
            else:
                return {"status": "unknown", "error": "Cannot serialize result"}
        
        return {
            "objective": plan.objective,
            "total_steps": len(plan.subtasks),
            "completed_steps": len([r for r in results if get_status(r) == "success"]),
            "failed_steps": len([r for r in results if get_status(r) == "failed"]),
            "results": [serialize_result(r) for r in results]
        }
    
    async def _execute_subtask(self, subtask: SubTask) -> ExecutionResult:
        """
        Execute a single subtask.
        
        Args:
            subtask: SubTask to execute
            
        Returns:
            ExecutionResult with status and output
        """
        logger.info(f"Executing step {subtask.step}: {subtask.action}")
        
        try:
            import time
            start_time = time.time()
            
            # Route to appropriate tool based on subtask.tool
            tool_name = subtask.tool
            result_data = None
            
            if tool_name == "rag_query":
                # Execute RAG query to get content from knowledge base
                from app.rag.query import semantic_search
                
                user_message = self.execution_context.get("user_message", subtask.action)
                logger.info(f"🔍 RAG query tool activated: {user_message[:100]}")
                
                # Extract entity/topic from user message for better filtering
                # Patterns: "quien es X", "sobre X", "de X", "resumen de X"
                entity_match = re.search(r'(?:quien es|quién es|sobre|de|resumen de|info(?:rmación)? de|datos de)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)', user_message, re.IGNORECASE)
                entity_filter = entity_match.group(1).strip() if entity_match else None
                
                if entity_filter:
                    logger.info(f"🎯 Detected entity/topic: '{entity_filter}' - will filter RAG results")
                
                # Detect if user mentions a specific file name
                file_filter = None
                # Match patterns like "CV.pdf", "daniel.txt", "archivo.xlsx"
                file_mention = re.search(r'([\w-]+\.(?:pdf|txt|docx?|xlsx?|csv|md))', user_message, re.IGNORECASE)
                if file_mention:
                    mentioned_file = file_mention.group(1)
                    file_id_stem = mentioned_file.rsplit('.', 1)[0]  # "CV.pdf" -> "CV"
                    logger.info(f"📄 Detected file mention: {mentioned_file} (file_id: {file_id_stem})")
                    # Filter by source (exact match) OR file_id (stem)
                    # ChromaDB metadata: {"source": "CV.pdf", "file_id": "CV", "chunk_index": 0}
                    file_filter = {"$or": [
                        {"file_id": {"$eq": file_id_stem}},
                        {"source": {"$eq": mentioned_file}}
                    ]}
                    self.execution_context["filter_by_file"] = mentioned_file
                
                try:
                    # Perform semantic search with optional file filter
                    logger.info(f"🔎 Calling semantic_search with filter_metadata: {file_filter}")
                    rag_results = semantic_search(user_message, top_k=5, filter_metadata=file_filter)
                    
                    if rag_results and len(rag_results) > 0:
                        # Filter by entity/topic if detected
                        if entity_filter:
                            # Keep only chunks that mention the entity
                            filtered_results = []
                            for r in rag_results:
                                doc_text = r.get("document", "")
                                # Case-insensitive search for entity
                                if entity_filter.lower() in doc_text.lower():
                                    filtered_results.append(r)
                            
                            if filtered_results:
                                logger.info(f"🎯 Filtered {len(rag_results)} results to {len(filtered_results)} mentioning '{entity_filter}'")
                                rag_results = filtered_results
                            else:
                                logger.warning(f"⚠️ No results mention '{entity_filter}', using all results")
                        
                        # Combine results into summary
                        texts = [r.get("document", "") for r in rag_results]
                        sources = list(set([r.get("metadata", {}).get("source", "unknown") for r in rag_results]))

                        # Log returned result identifiers for debugging file-scoped queries
                        try:
                            import hashlib
                            ids = [str(r.get("metadata", {}).get("source", "unknown")) for r in rag_results]
                            logger.info(f"🔎 RAG result sources: {ids}")
                            # Hash top texts to detect duplicates across requests
                            top_text_concat = "\n".join(texts[:3])
                            h = hashlib.md5(top_text_concat.encode('utf-8')).hexdigest()
                            logger.info(f"🔎 RAG summary MD5: {h}")
                        except Exception:
                            pass
                        
                        # Create summary from top results
                        summary = "\n\n".join(texts[:3])  # Top 3 chunks
                        
                        result_data = {
                            "status": "success",
                            "summary": summary,
                            "sources": sources,
                            "num_results": len(rag_results),
                            "message": f"Found {len(rag_results)} relevant documents"
                        }
                        logger.info(f"✅ RAG query successful: {len(rag_results)} results, {len(sources)} sources")
                    else:
                        result_data = {
                            "status": "success",
                            "summary": "",
                            "sources": [],
                            "num_results": 0,
                            "message": "No relevant documents found"
                        }
                        logger.warning("⚠️ RAG query returned no results")
                except Exception as e:
                    logger.error(f"❌ RAG query failed: {e}")
                    result_data = {
                        "status": "error",
                        "summary": "",
                        "sources": [],
                        "error": str(e),
                        "message": "RAG query failed"
                    }
            
            elif tool_name == "file_writer":
                # Generate PDF/Excel using RAG content with document_generator
                from app.tools.document_generator import get_document_generator
                generator = get_document_generator()
                
                logger.info(f"🎯 FileWriter tool activated for subtask: {subtask.action}")
                
                # Get RAG content from execution context
                rag_summary = self.execution_context.get("rag_summary", "")
                rag_sources = self.execution_context.get("rag_sources", [])
                user_message = self.execution_context.get("user_message", subtask.action)
                filter_by_file = self.execution_context.get("filter_by_file", None)
                
                logger.info(f"RAG context available - summary: {bool(rag_summary)}, sources: {len(rag_sources)}, filtered by: {filter_by_file}, message: {user_message[:50]}")
                
                # Extract subject from user message or use filtered file name
                if filter_by_file:
                    # Use the specific file name as subject
                    subject = filter_by_file.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
                else:
                    subject_match = re.search(r'(?:información|info|datos|detalles|análisis|analisis|reporte|informe).*?(?:de|sobre)\s+(\w+)', user_message.lower())
                    subject = subject_match.group(1).title() if subject_match else "Documento"
                
                # Detect file format requested
                is_pdf = any(kw in user_message.lower() or kw in subtask.action.lower() for kw in ["pdf", "documento"])
                is_excel = any(kw in user_message.lower() or kw in subtask.action.lower() for kw in ["excel", "hoja", "spreadsheet", "tabla"])
                
                # Default to PDF if not specified
                if not is_pdf and not is_excel:
                    is_pdf = True
                
                if is_pdf:
                    # Build content from RAG with structured data extraction
                    content = f"# Informe: {subject}\n\n"
                    
                    # Try to extract structured info from RAG summary
                    info_dict = {}
                    if rag_summary:
                        # DEBUG: Log RAG summary format
                        logger.info(f"🔍 RAG_SUMMARY length: {len(rag_summary)} chars")
                        logger.info(f"🔍 RAG_SUMMARY newlines: {rag_summary.count(chr(10))}")
                        logger.info(f"🔍 RAG_SUMMARY preview (first 500): {rag_summary[:500]}")
                        try:
                            import hashlib
                            summary_hash = hashlib.md5(rag_summary.encode('utf-8')).hexdigest()
                            logger.info(f"🔍 RAG_SUMMARY MD5: {summary_hash}")
                        except Exception:
                            pass
                        
                        # Parse key-value pairs from summary
                        lines = rag_summary.split('\n')
                        for line in lines:
                            # Match patterns like "Campo: Valor" or "Campo = Valor"
                            match = re.match(r'^([^:=]+)[:=]\s*(.+)$', line.strip())
                            if match:
                                key = match.group(1).strip()
                                value = match.group(2).strip()
                                info_dict[key] = value
                        
                        # Build structured content
                        if info_dict:
                            content += "## Datos Principales\n\n"
                            content += "TABLE_START\n"
                            for key, value in info_dict.items():
                                content += f"{key}|{value}\n"
                            content += "TABLE_END\n\n"
                        
                        # Add full summary
                        content += "## Información Completa\n\n"
                        content += rag_summary
                    else:
                        content += "No se encontró información específica en los documentos indexados.\n\n"
                        content += f"**Consulta realizada:** {user_message}"
                    
                    # Check if LLM response is available from context (generated after execution)
                    llm_response = self.execution_context.get("llm_response", "")
                    try:
                        import hashlib
                        llm_hash = hashlib.md5((llm_response or "").encode('utf-8')).hexdigest() if llm_response else None
                        logger.info(f"🔍 LLM response present: {bool(llm_response)}, MD5: {llm_hash}")
                    except Exception:
                        pass
                    # Prefer explicit LLM response when present (user-requested output
                    # should appear in the PDF even if it's shorter than the RAG summary)
                    if llm_response and llm_response.strip():
                        logger.info("🔎 Using LLM response as PDF content (preferred)")
                        content = f"# Informe: {subject}\n\n"
                        content += llm_response
                    else:
                        logger.info("🔎 Using RAG summary as PDF content")
                    
                    # Note: We intentionally do NOT append 'Fuentes Consultadas' into
                    # the PDF body to keep documents concise. Sources remain available
                    # in the metadata passed to the document generator.
                    
                    result_data = generator.generate_pdf(
                        title=f"Informe: {subject}",
                        content=content,
                        metadata={
                            "author": "ServiBot Agent",
                            "subject": subject,
                            "sources": ", ".join(rag_sources) if rag_sources else "None"
                        }
                    )
                elif is_excel:
                    # Build Excel from RAG - parse for structured data if possible
                    data = []
                    
                    # Try to extract structured information from RAG summary
                    if rag_summary:
                        # Simple parsing: look for lines with colons or structured data
                        lines = rag_summary.split('\n')
                        for line in lines:
                            if ':' in line and len(line.split(':')) == 2:
                                key, value = line.split(':', 1)
                                data.append({
                                    "Campo": key.strip(),
                                    "Valor": value.strip()
                                })
                    
                    # If no structured data found, add summary row
                    if not data:
                        data.append({
                            "Campo": "Consulta",
                            "Valor": user_message
                        })
                        data.append({
                            "Campo": "Respuesta",
                            "Valor": rag_summary[:500] if rag_summary else "Sin información"
                        })
                    
                    # Add sources
                    if rag_sources:
                        data.append({
                            "Campo": "Fuentes",
                            "Valor": ", ".join(rag_sources)
                        })
                    
                    result_data = generator.generate_excel(
                        title=f"Datos: {subject}",
                        data=data,
                        sheet_name="Análisis"
                    )
                
                # Log the result for debugging
                if result_data:
                    logger.info(f"✅ Document generated: {result_data.get('filename', 'Unknown')}")
                    logger.info(f"   Format: {result_data.get('format', 'Unknown')}")
                    logger.info(f"   Success: {result_data.get('success', False)}")
                else:
                    logger.error("❌ Document generation returned None")
            
            elif tool_name == "calendar":
                # Calendar tool - handle ALL calendar operations
                from app.tools.calendar_tool import get_calendar_tool
                calendar = get_calendar_tool()
                
                user_id = self.execution_context.get("user_id", "default_user")
                user_message = self.execution_context.get("user_message", "").lower()
                
                from datetime import datetime, timedelta
                
                # CHECK FOR CONFIRMATION FIRST - before keyword detection!
                confirmation_action = self.execution_context.get("confirmation_action")
                pending_data = self.execution_context.get("pending_action_data")
                
                if confirmation_action == "confirm" and pending_data:
                    # User confirmed - route to correct action based on action_type
                    action_params = pending_data.get("action_params", {})
                    action_type = pending_data.get("action_type", "")
                    
                    if action_type == "delete_calendar_event":
                        # DELETE confirmation
                        event_id = action_params.get("event_id")
                        logger.info(f"✅ Confirmation detected for DELETE event: {event_id}")
                        result_data = await calendar.execute({
                            "action": "delete",
                            "event_id": event_id
                        }, user_id=user_id)
                    
                    elif action_type == "update_calendar_event":
                        # UPDATE confirmation
                        event_id = action_params.get("event_id")
                        summary = action_params.get("summary")
                        logger.info(f"✅ Confirmation detected for UPDATE event: {event_id} to {summary}")
                        result_data = await calendar.execute({
                            "action": "update",
                            "event_id": event_id,
                            "summary": summary
                        }, user_id=user_id)
                    
                    else:
                        # CREATE confirmation (default)
                        summary = action_params.get("summary") or pending_data.get("summary")
                        start = action_params.get("start_time") or pending_data.get("start_time")
                        end = action_params.get("end_time") or pending_data.get("end_time")
                        logger.info(f"✅ Confirmation detected for CREATE event: {summary}")
                        result_data = await calendar.execute({
                            "action": "create",
                            "summary": summary,
                            "start_time": start,
                            "end_time": end
                        }, user_id=user_id)
                else:
                    # Not a confirmation - proceed with normal keyword detection
                    # Month mapping
                    month_map = {
                        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
                        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
                        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
                    }
                    
                    # Detect operation type
                    is_update = any(kw in user_message for kw in [
                        "cambiar", "cambia", "modificar", "modifica", "actualizar", "actualiza",
                        "renombrar", "renombra", "editar", "edita", "alterar", "altera",
                        "update", "change", "modify", "edit", "rename"
                    ])
                    
                    is_delete = any(kw in user_message for kw in [
                        "eliminar", "elimina", "borrar", "borra", "quitar", "quita",
                        "delete", "remove", "cancel", "cancelar"
                    ])
                    
                    is_create = any(kw in user_message for kw in [
                        "crear", "crea", "genera", "generar", "añadir", "añade", 
                        "agregar", "agrega", "nuevo", "nueva", "programar", "programa",
                        "create", "add", "schedule", "agendar", "agenda"
                    ])
                    
                    is_list = any(kw in user_message for kw in [
                        "listar", "lista", "muestra", "muéstrame", "dime", "cuál", "cuáles",
                        "próximos", "próximo", "siguiente", "agenda", "list", "show", "what",
                        "consultar", "consulta", "ver"
                    ])
                    
                    # PRIORITY: UPDATE > DELETE > CREATE > LIST
                    if is_update:
                        # UPDATE EVENT - Extract what to change and new values
                        logger.info(f"🔄 Detected UPDATE operation")
                        
                        # Find target event by date or current title
                        target_date = None
                        old_title = None
                        event_id = None
                        
                        # Extract date (to find the event)
                        date_match = re.search(r'(?:día|dia|del?)?\s*(\d{1,2})\s+(?:de\s+)?(\w+)(?:\s+(?:de\s+)?(\d{4}))?', user_message)
                        if date_match:
                            day = int(date_match.group(1))
                            month_name = date_match.group(2).lower()
                            year = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
                            month = month_map.get(month_name)
                            if month:
                                target_date = datetime(year, month, day)
                        
                        # Extract old title (to identify the event) - look for first quoted text
                        old_title_patterns = [
                            r'evento\s+[\'\"]([^\'\"]+)[\'\"]',  # evento 'titulo'
                            r'nombre\s+del\s+evento\s+[\'\"]([^\'\"]+)[\'\"]',  # nombre del evento 'titulo'
                            r'[\'\"]([^\'\"]+)[\'\"]\s+a\s+',  # 'titulo viejo' a 'titulo nuevo'
                        ]
                        for pattern in old_title_patterns:
                            old_title_match = re.search(pattern, user_message)
                            if old_title_match:
                                old_title = old_title_match.group(1)
                                logger.info(f"📝 Extracted old title: {old_title}")
                                break
                        
                        # Extract NEW title (what to change to)
                        new_title = None
                        new_title_patterns = [
                            r'por\s+el?\s+(?:siguiente\s+)?(?:título|titulo)\s+"([^"]+)"',
                            r'por\s+"([^"]+)"',
                            r'(?:título|titulo)\s+"([^"]+)"',
                            r'"([^"]+)"$'  # Last quoted text in message
                        ]
                        for pattern in new_title_patterns:
                            match = re.search(pattern, user_message)
                            if match:
                                new_title = match.group(1)
                                break
                        
                        if not new_title:
                            # Try to extract from uppercase words
                            words = user_message.split()
                            for i, word in enumerate(words):
                                if word in ["titulo", "título", "por"]:
                                    if i + 1 < len(words):
                                        new_title = ' '.join(words[i+1:]).strip('".,')
                                        break
                        
                        # Search for the event by date or title
                        if target_date:
                            # Search by date
                            time_min = target_date.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
                            time_max = (target_date + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat() + 'Z'
                            
                            events_result = await calendar.execute({
                                "action": "list",
                                "time_min": time_min,
                                "time_max": time_max,
                                "max_results": 10
                            }, user_id=user_id)
                        elif old_title:
                            # Search by title in upcoming events
                            time_min = datetime.utcnow().isoformat() + 'Z'
                            events_result = await calendar.execute({
                                "action": "list",
                                "time_min": time_min,
                                "max_results": 50
                            }, user_id=user_id)
                        else:
                            events_result = {"success": False}
                        
                        if events_result.get("success") and events_result.get("events"):
                            # Find event by title
                            target_event = None
                            if old_title:
                                for evt in events_result["events"]:
                                    if old_title.lower() in evt.get("summary", "").lower():
                                        target_event = evt
                                        break
                            if not target_event and events_result["events"]:
                                target_event = events_result["events"][0]
                            
                            if target_event:
                                event_id = target_event.get("id")
                                logger.info(f"🎯 Found event to update: {target_event.get('summary')} (ID: {event_id})")
                        
                        # Check if confirmation or initial request
                        confirmation_action_update = self.execution_context.get("confirmation_action")
                        pending_data_update = self.execution_context.get("pending_action_data")
                        
                        if confirmation_action_update == "confirm" and pending_data_update:
                            # User confirmed - execute update
                            action_params = pending_data_update.get("action_params", {})
                            event_id_confirmed = action_params.get("event_id") or pending_data_update.get("event_id")
                            new_title_confirmed = action_params.get("summary") or pending_data_update.get("summary")
                            
                            logger.info(f"✅ Confirmation detected for UPDATE, executing")
                            result_data = await calendar.execute({
                                "action": "update",
                                "event_id": event_id_confirmed,
                                "summary": new_title_confirmed
                            }, user_id=user_id)
                        elif event_id and new_title:
                            # Initial request - return pending_confirmation
                            # Ensure target_event is a dict before accessing keys
                            if isinstance(target_event, dict):
                                old_event_title = target_event.get("summary", "Evento")
                            else:
                                old_event_title = str(target_event) if target_event else "Evento"
                            result_data = {
                                "status": "pending_confirmation",
                                "action_type": "update_calendar_event",
                                "action_params": {
                                    "event_id": event_id,
                                    "summary": new_title
                                },
                                "confirmation_message": f"🔄 Voy a actualizar este evento:\n\n---\n**Título actual:** {old_event_title}\n**Nuevo título:** {new_title}\n---\n\n¿Confirmas el cambio?"
                            }
                        else:
                            result_data = {
                                "success": False,
                                "error": f"No pude identificar el evento a modificar. Evento encontrado: {event_id is not None}, Nuevo título: {new_title}"
                            }
                    
                    elif is_delete:
                        # DELETE EVENT
                        logger.info(f"🗑️ Detected DELETE operation")
                        
                        # Extract date or title to find the event
                        target_date = None
                        search_title = None
                        event_id = None
                        target_event = None
                        
                        # Extract date
                        date_match = re.search(r'(?:día|dia|del?)\s*(\d{1,2})\s+(?:de\s+)?(\w+)(?:\s+(?:de\s+)?(\d{4}))?', user_message)
                        if date_match:
                            day = int(date_match.group(1))
                            month_name = date_match.group(2).lower()
                            year = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
                            month = month_map.get(month_name)
                            if month:
                                target_date = datetime(year, month, day)
                                logger.info(f"📅 Searching events for {day}/{month}/{year}")
                        
                        # Extract title from message only when explicitly quoted: "evento "Título""
                        # Avoid capturing words like 'del' from phrases like 'evento del día'
                        title_match = re.search(r'(?:evento|event)\s+["\']([^"\']+)["\']', user_message, re.IGNORECASE)
                        if title_match:
                            search_title = title_match.group(1).strip()
                            logger.info(f"🔍 Searching event by title: {search_title}")
                        
                        # Search for the event
                        if target_date:
                            time_min = target_date.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
                            time_max = (target_date + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat() + 'Z'
                            
                            events_result = await calendar.execute({
                                "action": "list",
                                "time_min": time_min,
                                "time_max": time_max,
                                "max_results": 10
                            }, user_id=user_id)
                            
                            if events_result.get("success") and events_result.get("events"):
                                # Delete the first event from that day
                                target_event = events_result["events"][0]
                                if not isinstance(target_event, dict):
                                    logger.error(f"Unexpected event type: {type(target_event)} - {target_event}")
                                event_id = target_event.get("id") if isinstance(target_event, dict) else None
                                logger.info(f"🎯 Found event to delete: {target_event.get('summary') if isinstance(target_event, dict) else target_event} (ID: {event_id})")
                        elif search_title:
                            # Search by title in upcoming events
                            time_min = datetime.utcnow().isoformat() + 'Z'
                            events_result = await calendar.execute({
                                "action": "list",
                                "time_min": time_min,
                                "max_results": 50
                            }, user_id=user_id)
                            
                            if events_result.get("success") and events_result.get("events"):
                                # Find event by title (case-insensitive partial match)
                                for evt in events_result["events"]:
                                    if isinstance(evt, dict) and search_title.lower() in evt.get("summary", "").lower():
                                        target_event = evt
                                        event_id = evt.get("id")
                                        logger.info(f"🎯 Found event to delete: {evt.get('summary')} (ID: {event_id})")
                                        break
                                        break
                        
                        # Check if confirmation or initial request
                        confirmation_action_delete = self.execution_context.get("confirmation_action")
                        pending_data_delete = self.execution_context.get("pending_action_data")
                        
                        if confirmation_action_delete == "confirm" and pending_data_delete:
                            # User confirmed - execute delete
                            action_params = pending_data_delete.get("action_params", {})
                            event_id_confirmed = action_params.get("event_id") or pending_data_delete.get("event_id")
                            
                            logger.info(f"✅ Confirmation detected for DELETE, executing")
                            result_data = await calendar.execute({
                                "action": "delete",
                                "event_id": event_id_confirmed
                            }, user_id=user_id)
                        elif event_id and target_event:
                            # Initial request - return pending_confirmation
                            # Only access dict-like fields if we have a dict
                            if isinstance(target_event, dict):
                                event_title = target_event.get("summary", "Evento")
                                # Format date properly
                                event_start = target_event.get("start", {})
                                event_date_str = event_start.get("dateTime") if isinstance(event_start, dict) else (event_start.get("date") if isinstance(event_start, dict) else "")
                                if "T" in (event_date_str or ""):
                                    try:
                                        dt = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
                                        event_date_str = dt.strftime("%d/%m/%Y %H:%M")
                                    except:
                                        pass
                            else:
                                # Fallback when target_event is not a dict (string or other)
                                event_title = str(target_event)
                                event_date_str = ""

                            result_data = {
                                "status": "pending_confirmation",
                                "action_type": "delete_calendar_event",
                                "action_params": {
                                    "event_id": event_id,
                                    "event_title": event_title
                                },
                                "confirmation_message": f"🗑️ Voy a eliminar este evento:\n\n---\n**Título:** {event_title}\n**Fecha:** {event_date_str}\n---\n\n¿Confirmas que quieres eliminarlo?"
                            }
                        else:
                            result_data = {"success": False, "error": "No se pudo identificar el evento a eliminar. Intenta especificar la fecha o el título del evento."}
                    
                    elif is_create and not is_list:
                        # CREATE EVENT
                        logger.info(f"➕ Detected CREATE operation")
                        
                        # Check if this is a confirmation or initial request - CHECK FIRST!
                        confirmation_action = self.execution_context.get("confirmation_action")
                        pending_data = self.execution_context.get("pending_action_data")
                        
                        if confirmation_action == "confirm" and pending_data:
                            # User confirmed - create event with data from pending_data
                            # Extract from action_params if present, fallback to direct keys
                            action_params = pending_data.get("action_params", {})
                            summary = action_params.get("summary") or pending_data.get("summary")
                            start = action_params.get("start_time") or pending_data.get("start_time")
                            end = action_params.get("end_time") or pending_data.get("end_time")
                            
                            logger.info(f"✅ Confirmation detected, creating event: {summary}")
                            result_data = await calendar.execute({
                                "action": "create",
                                "summary": summary,
                                "start_time": start,
                                "end_time": end
                            }, user_id=user_id)
                        else:
                            # Initial request - extract parameters from user message
                            # Extract title
                            # Extract title - handle both explicit quotes and creative request
                            title = None
                            title_match = re.search(r'"([^"]+)"', user_message)
                            if title_match:
                                title = title_match.group(1)
                            else:
                                # Check if user wants creative title generation
                                creative_title_patterns = [
                                    r'(?:título|titulo|titula?o?)\s+(?:que\s+)?(?:quieras|creativo|apropiado|adecuado|inventa|invéntate)',
                                    r'(?:con|usando)\s+(?:el\s+)?(?:título|titulo)\s+(?:que\s+)?(?:quieras|prefieras|consideres)'
                                ]
                                is_creative_title = any(re.search(pattern, user_message, re.IGNORECASE) for pattern in creative_title_patterns)
                                
                                if not is_creative_title:
                                    # Try extracting explicit title
                                    titulo_match = re.search(r'(?:título|titulo|titula?o?)[:\s]+([^,\.]+)', user_message, re.IGNORECASE)
                                    if titulo_match:
                                        title = titulo_match.group(1).strip()
                            
                            # Extract date - handle both absolute and relative dates
                            event_start_time = None
                            event_end_time = None
                            
                            # Check for relative dates first (mañana, hoy, pasado mañana)
                            from datetime import datetime, timedelta
                            now = datetime.now()
                            
                            relative_date_match = re.search(r'\b(hoy|mañana|ma[ñn]ana|pasado\s+ma[ñn]ana|en\s+(\d+)\s+d[ií]as?)\b', user_message, re.IGNORECASE)
                            if relative_date_match:
                                relative_term = relative_date_match.group(1).lower()
                                if 'hoy' in relative_term:
                                    event_date = now.replace(hour=10, minute=0, second=0, microsecond=0)
                                elif 'mañana' in relative_term or 'manana' in relative_term:
                                    if 'pasado' in relative_term:
                                        event_date = (now + timedelta(days=2)).replace(hour=10, minute=0, second=0, microsecond=0)
                                    else:
                                        event_date = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
                                elif relative_date_match.group(2):  # "en X días"
                                    days = int(relative_date_match.group(2))
                                    event_date = (now + timedelta(days=days)).replace(hour=10, minute=0, second=0, microsecond=0)
                                else:
                                    event_date = None
                                
                                if event_date:
                                    event_start_time = event_date.isoformat()
                                    event_end_time = (event_date + timedelta(hours=1)).isoformat()
                            
                            # If no relative date, try absolute date (29 Enero 2026)
                            if not event_start_time:
                                date_match = re.search(r'(?:para|el)?\s*(\d{1,2})\s+(?:de\s+)?(\w+)\s+(?:de\s+)?(\d{4})', user_message)
                                if date_match:
                                    day = int(date_match.group(1))
                                    month_name = date_match.group(2).lower()
                                    year = int(date_match.group(3))
                                    month = month_map.get(month_name)
                                    
                                    if month:
                                        event_date = datetime(year, month, day, 10, 0)
                                        event_start_time = event_date.isoformat()
                                        event_end_time = (event_date + timedelta(hours=1)).isoformat()
                            
                            # Validation
                            if not event_start_time:
                                result_data = {"success": False, "error": "No se especificó fecha para el evento"}
                            else:
                                # If no title provided and not requesting creative title,
                                # allow the flow to continue and present a confirmation modal
                                # so the user can edit the title.
                                if is_creative_title:
                                    title = "__GENERATE_CREATIVE_TITLE__"
                                else:
                                    # Normalize missing title to empty string for modal
                                    title = title or ""

                                # Initial request - return pending_confirmation
                                try:
                                    dt = datetime.fromisoformat(event_start_time)
                                    formatted_date = dt.strftime("%d/%m/%Y %H:%M")
                                except:
                                    formatted_date = event_start_time

                                result_data = {
                                    "status": "pending_confirmation",
                                    "action_type": "create_calendar_event",
                                    "action_params": {
                                        "summary": title,
                                        "start_time": event_start_time,
                                        "end_time": event_end_time
                                    },
                                    "confirmation_message": f"📅 He preparado este evento:\n\n---\n**Título:** {title if title else '(sin título)'}\n**Fecha:** {formatted_date}\n---\n\n¿Quieres que lo cree?"
                                }
                    
                    elif is_list or ("list" in subtask.action.lower()):
                        # LIST EVENTS - Extract date filter if specified
                        time_min = None
                        time_max = None
                        max_results = 10
                        
                        # Try parsing Spanish month names
                        month_map = {
                            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
                            "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
                            "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12
                        }
                        
                        # Pattern: "DD Month YYYY" or "DD de Month de YYYY" or "día DD de Month"
                        date_match = re.search(r'(?:día|dia)?\s*(\d{1,2})\s+(?:de\s+)?(\w+)(?:\s+(?:de\s+)?(\d{4}))?', user_message)
                        if date_match:
                            day = int(date_match.group(1))
                            month_name = date_match.group(2).lower()
                            year = int(date_match.group(3)) if date_match.group(3) else datetime.now().year
                            month = month_map.get(month_name)
                            
                            if month:
                                # Set time range for that specific day
                                target_date = datetime(year, month, day, 0, 0, 0)
                                time_min = target_date.isoformat() + 'Z'
                                time_max = (target_date + timedelta(days=1)).isoformat() + 'Z'
                                max_results = 50  # Get more events to ensure we get all for the day
                                logger.info(f"📅 Filtering events for {day}/{month}/{year}")

                        # Try extracting a requested number of events (e.g., "3 eventos", "tres eventos")
                        num_match = re.search(r'(\d+)\s+(?:eventos|evento|próximos|próximo|siguientes)', user_message)
                        if num_match:
                            try:
                                max_results = int(num_match.group(1))
                            except Exception:
                                pass
                        else:
                            # Support Spanish number words
                            number_words = {
                                'uno': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
                                'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10
                            }
                            for w, v in number_words.items():
                                if re.search(rf'\b{w}\b\s+(?:eventos|evento|próximos|próximo|siguientes)', user_message):
                                    max_results = v
                                    break
                        
                        # If no specific date, use default (upcoming events)
                        if not time_min:
                            time_min = datetime.utcnow().isoformat() + 'Z'
                        
                        # List events with filters
                        params = {
                            "action": "list",
                            "max_results": max_results,
                            "time_min": time_min
                        }
                        
                        if time_max:
                            params["time_max"] = time_max
                        
                        result_data = await calendar.execute(params, user_id=user_id)
                    else:
                        # Fallback: check subtask action
                        if "calendar" in self.tools:
                            result_data = self.tools["calendar"](subtask.action)
                        else:
                            result_data = {"status": "error", "message": "Calendar tool not configured"}
            
            elif tool_name == "email":
                # Email tool - handle list_emails, read_email, AND send_email
                from app.tools.email_tool import get_email_tool
                email_tool = get_email_tool()
                
                user_id = self.execution_context.get("user_id", "default_user")
                user_message = self.execution_context.get("user_message", "").lower()
                original_message = self.execution_context.get("user_message", "")
                
                # PRIORITY: Check if this is a confirmation - execute directly with pending_data
                confirmation_action = self.execution_context.get("confirmation_action")
                pending_data = self.execution_context.get("pending_action_data")
                
                if confirmation_action == "confirm" and pending_data:
                    # Extract email params from pending_data
                    if pending_data.get("action_params"):
                        # New structure: {action_type, action_params}
                        params = pending_data["action_params"]
                    else:
                        # Direct structure: {to, subject, body}
                        params = pending_data
                    
                    logger.info(f"📧 Executing confirmed email send: to={params.get('to')}, subject={params.get('subject')}")
                    result_data = await email_tool.execute({
                        "action": "send",
                        "to": params.get("to"),
                        "subject": params.get("subject"),
                        "body": params.get("body")
                    }, user_id=user_id)
                else:
                    # Normal flow: detect operation type with priority: SEND > LIST > READ
                    # Pattern 1: Explicit send verb + email word
                    has_send_verb = any(kw in user_message for kw in [
                        "enviar", "envía", "envia", "mandar", "manda", "send"
                    ])
                    has_email_word = any(kw in user_message for kw in ["correo", "email", "mensaje", "mail"])
                    
                    # Pattern 2: "correo a", "email a", "mensaje a" pattern (implicit send)
                    has_recipient_pattern = any(pattern in user_message for pattern in [
                        "correo a ", "correo para ", "email a ", "email para ",
                        "mensaje a ", "mensaje para ", "mail a ", "mail para "
                    ])
                    
                    is_send = (has_send_verb and has_email_word) or has_recipient_pattern
                    
                    is_list = any(kw in user_message for kw in [
                        "listar", "lista", "muestra", "muéstrame", "dime", "correos", "emails", "list"
                    ])
                    
                    is_read = any(kw in user_message for kw in [
                        "leer", "lee", "ver", "read", "show"
                    ]) and not is_list
                    
                    if is_send:
                        # SEND EMAIL - Extract recipient, subject, and body
                        logger.info(f"📧 Processing EMAIL SEND. Original message: '{original_message}'")
                        to_email = None
                        subject = ""
                        body = ""
                        needs_llm_draft = False  # Flag to determine if LLM should draft the content
                        draft_instructions = ""  # Instructions for LLM to draft the email
                        
                        # Extract recipient (email address)
                        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                        email_match = re.search(email_pattern, original_message)
                        if email_match:
                            to_email = email_match.group(0)
                        else:
                            # Try patterns like "a X persona" or "a X"
                            # STRATEGY: Look for "a/para/to" (case insensitive) followed by a capitalized name
                            # This handles: "correo largo a Ana", "correo de 100 palabras para enviar a Ana"
                            to_match = re.search(
                                r'(?:a|to|para)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:[!❤️💙💚💛💜🧡💗💖💕💓💝💞💟]+)?(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:[!❤️💙💚💛💜🧡💗💖💕💓💝💞💟]+)?){0,2})',
                                original_message
                                # NO usar re.IGNORECASE porque necesitamos detectar mayúscula en el nombre
                            )
                            
                            # If not found, try case-insensitive for "a/para" but still require capital for name
                            if not to_match:
                                to_match = re.search(
                                    r'(?i)(?:a|para|to)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ!❤️💙💚💛💜🧡💗💖💕💓💝💞💟]+)',
                                    original_message
                                )
                            
                            if to_match:
                                potential_recipient = to_match.group(1).strip()
                                # Remove trailing ellipsis
                                potential_recipient = re.sub(r'\.{2,}$', '', potential_recipient).strip()
                                # Remove single trailing period or comma
                                potential_recipient = potential_recipient.rstrip('.,')
                                # Remove any trailing common words that aren't part of the name
                                potential_recipient = re.sub(r'\s+(un|una|el|la|de|del|con|y|que)\s*$', '', potential_recipient, flags=re.IGNORECASE).strip()
                                
                                # Clean name: remove emojis/special chars but keep original for search
                                clean_name = re.sub(r'[^\w\s\-\'áéíóúñÁÉÍÓÚÑüÜ]+', '', potential_recipient).strip()
                                
                                # Check if it's an email address or a contact name
                                if '@' in clean_name:
                                    to_email = clean_name
                                else:
                                    # It's a contact name - search with clean name
                                    logger.info(f"📇 Attempting to resolve contact name: '{clean_name}'")
                                    try:
                                        from app.tools.contacts_tool import get_contacts_tool
                                        contacts_tool = get_contacts_tool()
                                        search_result = await contacts_tool.execute({
                                            "action": "search",
                                            "query": clean_name
                                        }, user_id=user_id)
                                        
                                        if search_result.get("success") and search_result.get("contacts"):
                                            contacts = search_result["contacts"]
                                            logger.info(f"🔍 Found {len(contacts)} contacts matching '{clean_name}'")
                                            
                                            # Find first contact with valid email
                                            contact_with_email = None
                                            for contact in contacts:
                                                if contact.get("email"):
                                                    contact_with_email = contact
                                                    break
                                            
                                            if contact_with_email:
                                                to_email = contact_with_email["email"]
                                                contact_name = contact_with_email.get("name", clean_name)
                                                logger.info(f"✅ Resolved '{clean_name}' to {contact_name} <{to_email}>")
                                            else:
                                                # List contacts without email for debugging
                                                names_without_email = [c.get("name", "Sin nombre") for c in contacts[:3]]
                                                logger.warning(f"⚠️ Found {len(contacts)} contacts named '{clean_name}' but none have email: {names_without_email}")
                                                result_data = {
                                                    "success": False,
                                                    "error": f"El contacto '{clean_name}' no tiene email asociado"
                                                }
                                        else:
                                            logger.warning(f"❌ No contact found for: '{clean_name}'")
                                            result_data = {
                                                "success": False,
                                                "error": f"No se encontró el contacto '{clean_name}' en tus contactos de Google"
                                            }
                                    except Exception as e:
                                        logger.error(f"❌ Error resolving contact '{clean_name}': {str(e)}")
                                        result_data = {
                                            "success": False,
                                            "error": f"Error al buscar el contacto: {str(e)}"
                                        }
                        
                        # Extract subject - look for "asunto" or "subject" keywords
                        subject_match = re.search(r'(?:asunto|subject)[:\s]+([^,\.]+)', original_message, re.IGNORECASE)
                        if subject_match:
                            subject = subject_match.group(1).strip()
                        else:
                            subject = "Correo desde ServiBot"
                        
                        # INTELLIGENT CONTENT DETECTION
                        # Detect if user wants LLM to DRAFT content or wants to send SPECIFIC text
                        
                        # Initialize flags
                        body_found = False
                        needs_llm_draft = False
                        draft_instructions = ""
                        
                        # Patterns indicating user wants to send SPECIFIC text (literal message)
                        # HIGHEST PRIORITY - Very explicit patterns
                        literal_patterns = [
                            r'(?:con|y|el)\s+(?:este|el\s+siguiente|el)\s+(?:mensaje|texto|contenido)[:\s]+["\'](.+?)["\']',  # "con este mensaje: 'hola'"
                            r'(?:que\s+diga|diciendo|diciendole)[:\s]+["\'](.+?)["\']',  # "que diga: 'hola'"
                            r'mensaje[:\s]+["\'](.+?)["\']',  # "mensaje: 'hola'"
                            r'["\'](.+?)["\']',  # Any text in quotes (catches "hola" or 'hola')
                            r'(?:envia|manda)\s+(?:este|el\s+siguiente)\s+(?:mensaje|texto)[:\s]+(.+)',  # "envia este mensaje: hola"
                            r'(?:con|y)\s+el\s+texto[:\s]+(.+)',  # "con el texto: hola"
                        ]
                        
                        # Patterns indicating user wants LLM to DRAFT/GENERATE content
                        # MEDIUM PRIORITY - Explicit instructions for AI generation
                        draft_patterns = [
                            r'(?:que\s+)?(?:debes|deber|tiene\s+que|tienes\s+que)\s+(?:redactar|escribir|generar)',  # "que debes redactar"
                            r'(?:redacta|escribe|genera|crea)\s+(?:tu|tú)\s+(?:un|el)?\s*(?:mensaje|correo)?',  # "redacta tu un mensaje" or just "redacta tu"
                            r'(?:pidiendo|pidiéndole|solicitando|informando|notificando)\s+(?:que|para)',  # "pidiendo que"
                            r'(?:explicando|contando|mencionando|diciéndole|indicándole)\s+(?:que|sobre)',  # "diciendole que"
                            r'(?:preguntándole|preguntando)\s+(?:como|cómo|si|por|sobre)',  # "preguntandole como"
                            r'un\s+correo\s+(?:formal|informal|corto|largo|breve|detallado)',  # "un correo formal"
                            r'(?:con\s+un\s+tono|tono)\s+(?:formal|informal|amable|serio|profesional)',  # "con un tono formal"
                            r'(?:para\s+que|donde|en\s+(?:el\s+)?que)\s+(?:le|les)\s+(?:pida|solicite|informe|diga|digas|pregunte|preguntes)',  # "en el que le digas"
                            r'\bcomplet(?:a|ar|ado|e)\b',  # "completa el mensaje"
                            r'\bmejor(?:a|ar|ado|e)\b',  # "mejora el mensaje"
                            r'\bformaliz(?:a|ar|ado|e)\b',  # "formaliza el mensaje"
                        ]
                        

                        # Special-case: detect an explicit seed/draft labeled as 'Inicio:' or 'Borrador:'
                        # e.g. "Inicio: hola como estas? Completa y formaliza el mensaje"
                        seed_match = re.search(r'(?:inicio|borrador|borrador inicial)[:\s]+["\']?(.*?)["\']?(?:\.|$)', original_message, re.IGNORECASE | re.DOTALL)
                        if seed_match:
                            seed_text = seed_match.group(1).strip()
                            # If the user also includes drafting keywords, treat as draft with seed
                            if re.search(r'(?:complet(?:a|ar)|mejor(?:a|ar)|redacta|formaliz(?:a|ar)|genera|redacta)', user_message, re.IGNORECASE):
                                needs_llm_draft = True
                                # Keep the full original_message as instructions but include seed as context
                                draft_instructions = original_message
                                # Provide the seed as part of the prompt context later
                                body_found = True
                                logger.info(f"🤖 Detected DRAFT request with seed text: {seed_text[:80]}...")
                        
                        # First check for literal text (highest priority)
                        for pattern in literal_patterns:
                            literal_match = re.search(pattern, original_message, re.IGNORECASE | re.DOTALL)
                            if literal_match:
                                body = literal_match.group(1).strip()
                                # Remove quotes if present
                                body = body.strip('"\'')
                                body_found = True
                                needs_llm_draft = False
                                logger.info(f"📝 Detected LITERAL message: {body[:50]}...")
                                break
                        
                        # If no literal text found, check if user wants LLM to draft
                        if not body_found:
                            for pattern in draft_patterns:
                                match = re.search(pattern, user_message, re.IGNORECASE)
                                if match:
                                    needs_llm_draft = True
                                    # Extract the instructions for drafting
                                    # Remove the recipient part and "envia un correo a" parts
                                    draft_instructions = original_message
                                    if to_email:
                                        draft_instructions = draft_instructions.replace(to_email, "").strip()
                                    # Remove the "envia un correo a" prefix but keep the content instructions
                                    draft_instructions = re.sub(r'^(?:envia|envía|manda|mandar|correo|email)\s+(?:un\s+)?(?:correo|email|mensaje)\s+(?:a|para)\s+', '', draft_instructions, flags=re.IGNORECASE)
                                    # Keep the full context for LLM
                                    body_found = True  # Mark as found to skip fallback extraction
                                    logger.info(f"🤖 Detected DRAFT request (pattern: {pattern}) with instructions: {draft_instructions[:100]}...")
                                    break
                            
                            # Fallback: try to extract body normally if no pattern matched AND draft not requested
                            if not needs_llm_draft and not body_found:
                                body_match = re.search(r'(?:mensaje|contenido|body|text)[:\s]+(.+)', original_message, re.IGNORECASE)
                                if body_match:
                                    body = body_match.group(1).strip()
                                    body_found = True
                                else:
                                    # Use everything after recipient as body
                                    if to_email:
                                        parts = original_message.split(to_email, 1)
                                        if len(parts) > 1:
                                            body = parts[1].strip()
                                            # Remove common connecting words
                                            body = re.sub(r'^(?:con el siguiente mensaje|con el mensaje|mensaje|con|el siguiente|que diga|diciendo)[:\s]+', '', body, flags=re.IGNORECASE)
                                            body_found = True
                        
                        # If LLM draft is needed, generate content now
                        if needs_llm_draft and draft_instructions:
                            try:
                                from app.llm.local_client import generate_summary_from_prompt
                                
                                # Clean draft instructions - extract the actual content request
                                # Remove phrases like "en el que le digas", "un mensaje que debes redactar"
                                clean_instructions = re.sub(r'(?:en\s+(?:el\s+)?que\s+le\s+(?:digas|diga|preguntes|pregunte|cuentes|cuente|informes|informe)\s+)', '', draft_instructions, flags=re.IGNORECASE)
                                clean_instructions = re.sub(r'(?:un\s+mensaje\s+que\s+(?:debes|tienes\s+que)\s+redactar\s+(?:tu|tú)?\s+)', '', clean_instructions, flags=re.IGNORECASE)
                                clean_instructions = re.sub(r'(?:que\s+debes\s+redactar\s+(?:tu|tú)?\s+)', '', clean_instructions, flags=re.IGNORECASE)
                                clean_instructions = clean_instructions.strip()
                                
                                # Build prompt for email drafting with clear examples
                                draft_prompt = f"""Redacta un correo electrónico profesional basado en:

{clean_instructions}

REGLAS ESTRICTAS:
- Escribe SOLO el cuerpo del correo (saludo, mensaje principal, despedida)
- NO incluyas NUNCA frases meta como "Confirma para que lo envíe", "Déjame saber si quieres cambiar algo", "¿Te parece bien?"
- NO incluyas comentarios sobre el proceso de envío ni solicitudes de confirmación
- NO menciones nada sobre editar, revisar o confirmar el correo
- Escribe como si el correo YA estuviera listo para enviarse
- Máximo 100 palabras si se especifica, sino 3-4 líneas
- Tono amable pero directo

Correo:"""
                                
                                # Get conversation history from context for better drafting
                                conversation_history = self.execution_context.get("conversation_history", [])
                                # Sanitize history to prevent circular JSON and limit size
                                conversation_history = sanitize_conversation_history(conversation_history, max_messages=3)
                                
                                if conversation_history and len(conversation_history) > 1:
                                    # Add recent context (last 3 messages max)
                                    context_messages = conversation_history[-3:]
                                    context_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in context_messages if isinstance(msg, dict)])
                                    draft_prompt = f"Contexto de la conversación:\n{context_text}\n\n{draft_prompt}"
                                
                                # Generate email body with LLM
                                body = generate_summary_from_prompt(draft_prompt, max_tokens=300)
                                body = body.strip()
                                logger.info(f"✨ LLM generated email body: {body[:100]}...")
                            except Exception as e:
                                logger.error(f"❌ Error generating email with LLM: {e}")
                                # Fallback: use instructions as body
                                body = draft_instructions
                        
                        # Validate required fields and always return a confirmation
                        if not to_email:
                            result_data = {"success": False, "error": "No se especificó destinatario del correo"}
                            logger.error(f"❌ Email send failed: no recipient found. Original: '{original_message[:100]}'")
                        else:
                            # Ensure there's some body content to show in the preview.
                            if not body:
                                # Prefer any draft instructions, otherwise use a short placeholder
                                body = draft_instructions.strip() if draft_instructions else "Hola, te escribo para saber cómo estás."
                            
                            # Clean any accidental meta-text from body using multiple patterns
                            body = re.sub(r'\s*Confirma para que lo envíe\.?\s*$', '', body, flags=re.IGNORECASE)
                            body = re.sub(r'\s*¿Te parece bien\?\s*$', '', body, flags=re.IGNORECASE)
                            body = re.sub(r'\s*Déjame saber si quieres cambiar algo\.?\s*$', '', body, flags=re.IGNORECASE)
                            body = re.sub(r'\s*¿Quieres que lo envíe\?\s*$', '', body, flags=re.IGNORECASE)
                            body = body.strip()

                            # Initial request - return pending_confirmation so frontend shows modal
                            result_data = {
                                "status": "pending_confirmation",
                                "action_type": "send_email",
                                "action_params": {
                                    "to": to_email,
                                    "subject": subject,
                                    "body": body
                                },
                                "confirmation_message": f"📧 He preparado este email:\n\n---\n**Para:** {to_email}\n**Asunto:** {subject}\n**Cuerpo:** {body}\n---\n\n¿Quieres que lo envíe?"
                            }
                    
                    elif is_list:
                        # LIST EMAILS - Extract max_results from user message
                        max_results = 10  # default
                        # Try to extract digit numbers first
                        number_match = re.search(r'(\d+)\s+(?:correos|emails|mensajes|últimos|ultimos)', user_message)
                        if number_match:
                            max_results = int(number_match.group(1))
                        else:
                            # Support Spanish number words (uno, dos, tres...)
                            number_words = {
                                'uno': 1, 'dos': 2, 'tres': 3, 'cuatro': 4, 'cinco': 5,
                                'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10
                            }
                            for word, val in number_words.items():
                                if re.search(rf'\b{word}\b\s+(?:correos|emails|mensajes|últimos|ultimos)', user_message):
                                    max_results = val
                                    break
                        
                        # Build query: use None to let email_tool apply default (category:primary)
                        query = None
                        
                        # List emails with extracted parameters
                        result_data = await email_tool.execute({
                            "action": "list", 
                            "max_results": max_results,
                            "query": query
                        }, user_id=user_id)
                    
                    elif is_read:
                        # READ EMAIL - would need message_id from context
                        result_data = {"success": False, "error": "Leer correo específico requiere ID de mensaje"}
                    
                    else:
                        # Fallback
                        result_data = {"success": False, "error": "No se pudo determinar la acción de email"}
            
            elif tool_name == "ocr":
                # OCR tool
                from app.tools.ocr_tool import get_ocr_tool
                ocr = get_ocr_tool()
                # Note: Would need image path from context
                result_data = {"status": "success", "message": "OCR tool available"}
            
            elif tool_name in self.tools:
                # Use registered tool (mocks or custom)
                tool_func = self.tools[tool_name]
                result_data = tool_func(subtask.action)
            
            else:
                # Default: simulate execution
                result_data = {
                    "status": "success",
                    "message": f"Simulated execution of: {subtask.action}",
                    "tool": tool_name
                }
            
            execution_time = time.time() - start_time
            
            # Extra debugging for file generation
            if tool_name == "file_writer":
                logger.info(f"🔍 FILE_WRITER RESULT CHECK:")
                logger.info(f"   result_data type: {type(result_data)}")
                logger.info(f"   result_data: {result_data}")
            
            # Check if result has pending_confirmation status
            if isinstance(result_data, dict) and result_data.get("status") == "pending_confirmation":
                return ExecutionResult(
                    step=subtask.step,
                    status="pending_confirmation",
                    tool_used=tool_name,
                    result=result_data,
                    error=None,
                    execution_time_seconds=execution_time
                )

            # Determine success/failure based on tool result content
            final_status = "success"
            final_error = None
            if isinstance(result_data, dict):
                # Tools may return {'success': True/False, ...} or {'status': 'error'/'failed', ...}
                if "success" in result_data:
                    if not result_data.get("success"):
                        final_status = "failed"
                        final_error = result_data.get("error") or result_data.get("message")
                elif result_data.get("status") in ("error", "failed"):
                    final_status = "failed"
                    final_error = result_data.get("error") or result_data.get("message")

            result = ExecutionResult(
                step=subtask.step,
                status=final_status,
                tool_used=tool_name,
                result=result_data,
                error=final_error,
                execution_time_seconds=execution_time
            )
            
            # Extra debugging for execution result
            if tool_name == "file_writer":
                logger.info(f"🔍 EXECUTION RESULT:")
                logger.info(f"   step: {result.step}")
                logger.info(f"   status: {result.status}")
                logger.info(f"   result keys: {list(result.result.keys()) if isinstance(result.result, dict) else 'N/A'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing step {subtask.step}: {str(e)}")
            return ExecutionResult(
                step=subtask.step,
                status="failed",
                tool_used=subtask.tool,
                result=None,
                error=str(e)
            )


# Global executor instance
executor = Executor()
