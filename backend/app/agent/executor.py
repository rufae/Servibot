"""
Agent Executor Module
Executes planned tasks using available tools.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.agent.planner import ExecutionPlan, SubTask
from app.core.config import settings

logger = logging.getLogger(__name__)


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
            
            # Stop execution if critical step failed
            if result.status == "failed" and subtask.step in [1, 2]:
                logger.error(f"Critical step {subtask.step} failed, stopping execution")
                break
        
        return {
            "objective": plan.objective,
            "total_steps": len(plan.subtasks),
            "completed_steps": len([r for r in results if r.status == "success"]),
            "failed_steps": len([r for r in results if r.status == "failed"]),
                "results": [r.model_dump() for r in results]
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
            
            if tool_name == "file_writer":
                # Generate PDF/Excel using RAG content if available
                from app.tools.file_writer import get_file_writer
                writer = get_file_writer()
                
                logger.info(f"FileWriter tool activated for subtask: {subtask.action}")
                
                # Get RAG content from execution context
                rag_summary = self.execution_context.get("rag_summary", "")
                rag_sources = self.execution_context.get("rag_sources", [])
                user_message = self.execution_context.get("user_message", subtask.action)
                
                logger.info(f"RAG context available - summary: {bool(rag_summary)}, sources: {len(rag_sources)}, message: {user_message[:50]}")
                
                # Extract subject from user message (e.g., "Laura", "Daniel")
                import re
                subject_match = re.search(r'(?:información|info|datos|detalles).*?(?:de|sobre)\s+(\w+)', user_message.lower())
                subject = subject_match.group(1).title() if subject_match else "Documento"
                
                # Extract intent from action
                if "pdf" in subtask.action.lower():
                    # Build content from RAG
                    content = f"Generado por ServiBot\n\n"
                    content += f"Consulta: {user_message}\n\n"
                    content += "=" * 50 + "\n\n"
                    
                    if rag_summary:
                        content += rag_summary
                    else:
                        content += "No se encontró información específica en los documentos indexados."
                    
                    if rag_sources:
                        content += f"\n\n{'=' * 50}\n\nFuentes:\n"
                        for src in rag_sources:
                            content += f"  • {src}\n"
                    
                    result_data = writer.generate_pdf(
                        title=f"Información sobre {subject}",
                        content=content,
                        metadata={"Generated": "ServiBot Agent", "Subject": subject, "Sources": rag_sources}
                    )
                elif "excel" in subtask.action.lower():
                    # Build Excel from RAG
                    headers = {"Info": ["Campo", "Valor"]}
                    rows = [
                        ["Consulta", user_message],
                        ["Respuesta", rag_summary[:500] if rag_summary else "Sin información"],
                        ["Fuentes", ", ".join(rag_sources) if rag_sources else "Ninguna"]
                    ]
                    sheets = {"Info": rows}
                    
                    result_data = writer.generate_excel(
                        filename=f"{subject.lower()}_info.xlsx",
                        sheets=sheets,
                        headers=headers
                    )
                else:
                    result_data = {"status": "success", "message": "File writer tool called"}
            
            elif tool_name == "calendar":
                # Calendar tool - handle ALL calendar operations
                from app.tools.calendar_tool import get_calendar_tool
                calendar = get_calendar_tool()
                
                user_id = self.execution_context.get("user_id", "default_user")
                user_message = self.execution_context.get("user_message", "").lower()
                
                import re
                from datetime import datetime, timedelta
                
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
                    "crear", "crea", "añadir", "añade", "agregar", "agrega", 
                    "nuevo", "nueva", "create", "add", "schedule", "agendar"
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
                    
                    # Extract old title (to identify the event) - look for "evento" or quoted text
                    old_title_match = re.search(r'(?:evento|event)(?:\s+del?)?(?:\s+día)?\s+(?:\d{1,2})\s+\w+\s*\d{4}', user_message)
                    if not old_title_match:
                        # Try to find quoted old title
                        old_title_match = re.search(r'de\s+"([^"]+)"', user_message)
                        if old_title_match:
                            old_title = old_title_match.group(1)
                    
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
                    
                    # First, list events from that date to get event_id
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
                            # Get first event from that day (or match by old_title if available)
                            target_event = events_result["events"][0]
                            if old_title:
                                for evt in events_result["events"]:
                                    if old_title.lower() in evt.get("summary", "").lower():
                                        target_event = evt
                                        break
                            
                            event_id = target_event.get("id")
                            logger.info(f"🎯 Found event to update: {target_event.get('summary')} (ID: {event_id})")
                    
                    # Update the event
                    if event_id and new_title:
                        result_data = await calendar.execute({
                            "action": "update",
                            "event_id": event_id,
                            "summary": new_title
                        }, user_id=user_id)
                    else:
                        result_data = {
                            "success": False,
                            "error": f"No pude identificar el evento a modificar. Evento encontrado: {event_id is not None}, Nuevo título: {new_title}"
                        }
                
                elif is_delete:
                    # DELETE EVENT
                    logger.info(f"🗑️ Detected DELETE operation")
                    # TODO: Implement delete logic similar to update
                    result_data = {"success": False, "error": "Delete operation not fully implemented yet"}
                
                elif is_create and not is_list:
                    # CREATE EVENT - Extract all parameters from user message
                    logger.info(f"➕ Detected CREATE operation")
                    
                    # Extract title
                    title = None
                    title_match = re.search(r'"([^"]+)"', user_message)
                    if title_match:
                        title = title_match.group(1)
                    else:
                        titulo_match = re.search(r'(?:título|titulo|titula?o?)[:\s]+([^,\.]+)', user_message)
                        if titulo_match:
                            title = titulo_match.group(1).strip()
                    
                    if not title:
                        result_data = {"success": False, "error": "No se especificó título para el evento"}
                    else:
                        # Extract date
                        start_time = None
                        end_time = None
                        date_match = re.search(r'(?:para|el)?\s*(\d{1,2})\s+(?:de\s+)?(\w+)\s+(?:de\s+)?(\d{4})', user_message)
                        if date_match:
                            day = int(date_match.group(1))
                            month_name = date_match.group(2).lower()
                            year = int(date_match.group(3))
                            month = month_map.get(month_name)
                            
                            if month:
                                event_date = datetime(year, month, day, 10, 0)
                                start_time = event_date.isoformat()
                                end_time = (event_date + timedelta(hours=1)).isoformat()
                        
                        if not start_time:
                            result_data = {"success": False, "error": "No se especificó fecha para el evento"}
                        else:
                            # Create event with extracted parameters ONLY
                            result_data = await calendar.execute({
                                "action": "create",
                                "summary": title,
                                "start_time": start_time,
                                "end_time": end_time
                            }, user_id=user_id)
                
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
                
                import re
                
                # Detect operation type with priority: SEND > LIST > READ
                is_send = any(kw in user_message for kw in [
                    "enviar", "envía", "envia", "mandar", "manda", "send", "email"
                ]) and any(kw in user_message for kw in ["correo", "email", "mensaje"])
                
                is_list = any(kw in user_message for kw in [
                    "listar", "lista", "muestra", "muéstrame", "dime", "correos", "emails", "list"
                ])
                
                is_read = any(kw in user_message for kw in [
                    "leer", "lee", "ver", "read", "show"
                ]) and not is_list
                
                if is_send:
                    # SEND EMAIL - Extract recipient, subject, and body
                    to_email = None
                    subject = ""
                    body = ""
                    
                    # Extract recipient (email address)
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    email_match = re.search(email_pattern, original_message)
                    if email_match:
                        to_email = email_match.group(0)
                    else:
                        # Try patterns like "a X persona" or "a X"
                        to_match = re.search(r'(?:a|to)\s+([^\s,]+(?:\s+[^\s,]+)?)', user_message)
                        if to_match:
                            to_email = to_match.group(1).strip()
                    
                    # Extract subject - look for "asunto" or "subject" keywords
                    subject_match = re.search(r'(?:asunto|subject)[:\s]+([^,\.]+)', original_message, re.IGNORECASE)
                    if subject_match:
                        subject = subject_match.group(1).strip()
                    else:
                        subject = "Correo desde ServiBot"
                    
                    # Extract body/message - look for "mensaje" or "contenido" keywords or quoted text
                    body_match = re.search(r'(?:mensaje|contenido|body|text)[:\s]+(.+)', original_message, re.IGNORECASE)
                    if body_match:
                        body = body_match.group(1).strip()
                    else:
                        # Try to find quoted text
                        quote_match = re.search(r'["\'](.+?)["\']', original_message)
                        if quote_match:
                            body = quote_match.group(1)
                        else:
                            # Use everything after recipient as body
                            if to_email:
                                parts = original_message.split(to_email, 1)
                                if len(parts) > 1:
                                    body = parts[1].strip()
                                    # Remove common connecting words
                                    body = re.sub(r'^(?:con el siguiente mensaje|con el mensaje|mensaje|con|el siguiente|que diga|diciendo)[:\s]+', '', body, flags=re.IGNORECASE)
                    
                    # Validate required fields
                    if not to_email:
                        result_data = {"success": False, "error": "No se especificó destinatario del correo"}
                    elif not body:
                        result_data = {"success": False, "error": "No se especificó mensaje del correo"}
                    else:
                        # Send email with extracted parameters
                        result_data = await email_tool.execute({
                            "action": "send",
                            "to": to_email,
                            "subject": subject,
                            "body": body
                        }, user_id=user_id)
                
                elif is_list:
                    # LIST EMAILS - Extract max_results from user message
                    max_results = 10  # default
                    number_match = re.search(r'(\d+)\s+(?:correos|emails|mensajes|últimos|ultimos)', user_message)
                    if number_match:
                        max_results = int(number_match.group(1))
                    
                    # Build query for inbox only (exclude spam/trash)
                    query = "in:inbox -in:spam -in:trash"
                    
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
            
            result = ExecutionResult(
                step=subtask.step,
                status="success",
                tool_used=tool_name,
                result=result_data,
                execution_time_seconds=execution_time
            )
            
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
