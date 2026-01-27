"""
Chat API Endpoint
Handles user chat interactions with the ServiBot agent.
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timedelta
import re
import logging

from app.agent.planner import planner
from app.agent.executor import executor
from app.agent.evaluator import evaluator
from app.agent.intent_detector import get_intent_detector
from app.core.config import settings
from app.llm.local_client import summarize_texts
from app.auth.jwt_handler import verify_token
from app.db.sqlite_client import get_sqlite_client
import os

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message request model."""
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    confirmation_action: Optional[str] = None  # 'confirm', 'cancel', or 'edit'
    pending_action_data: Optional[Dict[str, Any]] = None  # Data for confirmed action
    conversation_history: Optional[List[Dict[str, str]]] = None  # Previous messages for context (for conversational memory)


class ChatResponse(BaseModel):
    """Chat message response model."""
    response: str
    conversation_id: str
    timestamp: str
    plan: Optional[List[Dict[str, Any]]] = None
    execution: Optional[Dict[str, Any]] = None
    evaluation: Optional[Dict[str, Any]] = None
    # `sources` can be either list of strings (filenames) or list of dicts with document data
    sources: Optional[Union[List[str], List[Dict[str, Any]]]] = None
    generated_file: Optional[Dict[str, str]] = None  # File info if executor generated one
    pending_confirmation: Optional[Dict[str, Any]] = None  # Pending action requiring confirmation


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage, authorization: Optional[str] = Header(None)):
    """
    Main chat endpoint that processes user messages through the agent.

    Flow implemented:
    1. Planner generates an ExecutionPlan from the user message.
    2. Executor runs the plan. Using "confirmación automática": all steps are auto-confirmed.
    3. Evaluator assesses the execution results.
    4. Return structured response with plan, execution results and evaluation.
    """
    try:
        logger.info(f"Received chat message: {message.message[:50] if message.message else '(confirmation)'}...")
        
        # Prepare execution context with conversation history
        execution_context = {}
        if message.conversation_history:
            execution_context["conversation_history"] = message.conversation_history
            logger.info(f"📚 Loaded {len(message.conversation_history)} messages for conversational context")
        
        # Handle confirmation responses (check BEFORE generating plan)
        if message.confirmation_action and message.pending_action_data:
            if message.confirmation_action == 'cancel':
                return ChatResponse(
                    response="✅ Acción cancelada.",
                    conversation_id=message.conversation_id or f"conv_{datetime.utcnow().timestamp()}",
                    timestamp=datetime.utcnow().isoformat()
                )
            elif message.confirmation_action == 'edit':
                # User wants to edit - provide context for re-drafting
                # Extract the pending action to help user modify it
                pending = message.pending_action_data or {}
                context_msg = ""
                if pending.get('action_type') == 'send_email':
                    params = pending.get('action_params', {})
                    context_msg = f"El correo actual es para {params.get('to', 'destinatario')} con asunto '{params.get('subject', 'sin asunto')}' y mensaje: {params.get('body', 'sin mensaje')}. ¿Qué quieres cambiar?"
                else:
                    context_msg = "Por favor, indícame los cambios que quieres realizar."
                
                return ChatResponse(
                    response=f"✏️ {context_msg}",
                    conversation_id=message.conversation_id or f"conv_{datetime.utcnow().timestamp()}",
                    timestamp=datetime.utcnow().isoformat(),
                    pending_confirmation=pending  # Keep pending action for context
                )
            elif message.confirmation_action == 'confirm':
                # Bypass planner: build a minimal ExecutionPlan from pending_action_data
                pending = message.pending_action_data or {}
                action_params = pending.get('action_params', {})
                
                # Determine tool and action based on pending keys
                from app.agent.planner import SubTask, ExecutionPlan
                subtasks = []
                action_type = pending.get('action_type', '')
                
                if action_params.get('to') or action_type == 'send_email':
                    # Email send
                    subtasks = [
                        SubTask(
                            step=1,
                            action="Send email (confirmed)",
                            tool="email",
                            estimated_time_minutes=1,
                            requires_confirmation=False,
                            success_criteria="Email sent successfully"
                        )
                    ]
                elif action_params.get('event_id') and action_type == 'delete_calendar_event':
                    # Delete calendar event
                    subtasks = [
                        SubTask(
                            step=1,
                            action="Delete calendar event (confirmed)",
                            tool="calendar",
                            estimated_time_minutes=1,
                            requires_confirmation=False,
                            success_criteria="Event deleted"
                        )
                    ]
                elif action_params.get('event_id') and action_params.get('summary') and action_type == 'update_calendar_event':
                    # Update calendar event
                    subtasks = [
                        SubTask(
                            step=1,
                            action="Update calendar event (confirmed)",
                            tool="calendar",
                            estimated_time_minutes=1,
                            requires_confirmation=False,
                            success_criteria="Event updated"
                        )
                    ]
                elif action_params.get('summary') and action_params.get('start_time'):
                    # Create calendar event
                    subtasks = [
                        SubTask(
                            step=1,
                            action="Create calendar event (confirmed)",
                            tool="calendar",
                            estimated_time_minutes=1,
                            requires_confirmation=False,
                            success_criteria="Event created"
                        )
                    ]
                else:
                    # Unknown pending action, fallback to planner
                    subtasks = []

                if subtasks:
                    plan = ExecutionPlan(
                        objective=f"Confirmed action: {pending.get('action_type', 'user_confirm')}",
                        subtasks=subtasks,
                        total_estimated_time=sum(t.estimated_time_minutes for t in subtasks),
                        requires_user_confirmation=False,
                        risk_level="low"
                    )

                    # Extract user_id from JWT token
                    user_id = "default_user"  # Fallback
                    try:
                        if authorization:
                            token = authorization.replace('Bearer ', '') if 'Bearer ' in authorization else authorization
                            uid = verify_token(token)
                            if uid:
                                db = get_sqlite_client()
                                user = db.get_user_by_id(int(uid))
                                if user:
                                    user_id = str(user.get('id'))  # Convert to string
                                    logger.info(f"✅ Using user_id: {user_id} for confirmed action")
                    except Exception as e:
                        logger.warning(f"Could not extract user_id: {e}")
                        user_id = "default_user"

                    # Prepare execution context to include confirmation data
                    execution_context = {
                        "user_message": message.message,
                        "original_context": message.context or {},
                        "confirmation_action": message.confirmation_action,
                        "pending_action_data": pending,
                        "user_id": user_id  # Add user_id for tools
                    }

                    exec_results = await executor.execute_plan(plan, user_confirmations={1: True}, context=execution_context)
                    evaluation = evaluator.evaluate_results(exec_results)

                    # Prepare response from exec_results
                    response_text = "Acción confirmada y ejecutada."
                    # Check for email send results
                    for result in exec_results.get('results', []):
                        if result.get('tool_used') == 'email' and isinstance(result.get('result'), dict):
                            rd = result.get('result')
                            if rd.get('success') and rd.get('message_id'):
                                response_text = f"✅ Correo enviado exitosamente: {rd.get('message_id')}"
                            elif rd.get('success') and rd.get('message'):
                                response_text = f"✅ {rd.get('message')}"
                        elif result.get('tool_used') == 'calendar' and isinstance(result.get('result'), dict):
                            rd = result.get('result')
                            if action_type == 'delete_calendar_event' and rd.get('success'):
                                response_text = f"✅ Evento eliminado del calendario"
                            elif action_type == 'update_calendar_event' and rd.get('success'):
                                response_text = f"✅ Evento actualizado en el calendario"
                            elif rd.get('success') and rd.get('event_id'):
                                response_text = f"✅ Evento creado exitosamente en el calendario"
                            elif rd.get('success'):
                                response_text = f"✅ Operación de calendario completada"
                            elif rd.get('error'):
                                response_text = f"❌ Error: {rd.get('error')}"

                    return ChatResponse(
                        response=response_text,
                        conversation_id=message.conversation_id or f"conv_{datetime.utcnow().timestamp()}",
                        timestamp=datetime.utcnow().isoformat(),
                        plan=[s.model_dump() for s in plan.subtasks],
                        execution=exec_results,
                        evaluation=evaluation
                    )
        
        # For empty messages without confirmation, return early
        if not message.message or not message.message.strip():
            return ChatResponse(
                response="Por favor, envía un mensaje.",
                conversation_id=message.conversation_id or f"conv_{datetime.utcnow().timestamp()}",
                timestamp=datetime.utcnow().isoformat()
            )
        plan = planner.generate_plan(message.message, message.context)

        # 2) Build auto-confirmations (confirm all steps)
        user_confirmations: Dict[int, bool] = {s.step: True for s in plan.subtasks}

        # 3) Prepare context for executor (will include RAG results if available)
        exec_context = {
            "user_message": message.message,
            "original_context": message.context or {},
            "confirmation_action": message.confirmation_action,
            "pending_action_data": message.pending_action_data,
        }
        
        # Add conversation history from prepared context
        if execution_context.get("conversation_history"):
            exec_context["conversation_history"] = execution_context["conversation_history"]

        # If Authorization header is provided and valid, attach minimal user info
        user_info = None
        user_id = "default_user"  # Fallback
        try:
            if authorization:
                token = authorization.replace('Bearer ', '') if 'Bearer ' in authorization else authorization
                uid = verify_token(token)
                if uid:
                    db = get_sqlite_client()
                    user = db.get_user_by_id(int(uid))
                    if user:
                        user_info = {
                            "id": user.get('id'),
                            "email": user.get('email'),
                            "name": user.get('name'),
                            # Do NOT include tokens or credentials here
                        }
                        user_id = str(user.get('id'))  # Convert to string
                        exec_context['user'] = user_info
                        exec_context['user_id'] = user_id  # Add user_id for tools
                        logger.info(f"✅ Using user_id: {user_id} for chat execution")
        except Exception as e:
            # Fail silently: do not break chat for auth errors
            logger.warning(f"Auth error in chat: {e}")
            user_info = None
            exec_context['user_id'] = user_id  # Set fallback

        # 3) Execute the plan
        exec_results = await executor.execute_plan(plan, user_confirmations=user_confirmations, context=exec_context)
        
        # Check if any action requires confirmation
        pending_confirmation = None
        for result in exec_results.get("results", []):
            if result.get("status") == "pending_confirmation":
                pending_confirmation = result.get("result")
                logger.info(f"🔔 Action requires confirmation: {pending_confirmation.get('action_type')}")
                break
        
        # If confirmation is pending, return early with confirmation request
        if pending_confirmation:
            confirmation_msg = pending_confirmation.get("confirmation_message", "¿Quieres continuar con esta acción?")
            return ChatResponse(
                response=confirmation_msg,
                conversation_id=message.conversation_id or f"conv_{datetime.utcnow().timestamp()}",
                timestamp=datetime.utcnow().isoformat(),
                plan=[s.model_dump() for s in plan.subtasks],
                execution=exec_results,
                pending_confirmation=pending_confirmation
            )

        # 4) Evaluate results
        evaluation = evaluator.evaluate_results(exec_results)

        # Check if executor returned data from calendar/email tools
        tool_response = None
        tool_response_parts = []
        for result in exec_results.get("results", []):
            if result.get("status") == "success":
                result_data = result.get("result", {})
                tool_used = result.get("tool_used")
                
                # Calendar tool: format events for response
                if tool_used == "calendar" and isinstance(result_data, dict) and result_data.get("success"):
                    # Check if it's a list, create, or update operation
                    if "events" in result_data:
                        # List events
                        events = result_data.get("events", [])
                        if events:
                            event_list = []
                            for event in events[:10]:  # Limit to 10 events
                                summary = event.get("summary", "Sin título")
                                start = event.get("start", "")
                                # Format date nicely
                                try:
                                    if "T" in start:
                                        dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                                        formatted = dt.strftime("%d/%m/%Y %H:%M")
                                    else:
                                        formatted = start
                                    event_list.append(f"• **{summary}** - {formatted}")
                                except:
                                    event_list.append(f"• **{summary}** - {start}")
                            
                            count = result_data.get("count", len(events))
                            tool_response_parts.append(f"📅 Tienes {count} eventos próximos:\n\n" + "\n".join(event_list))
                    
                    elif "event_id" in result_data and "start" in result_data:
                        # Event created
                        summary = result_data.get("summary", "Evento")
                        start = result_data.get("start", "")
                        try:
                            if "T" in start:
                                dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                                formatted = dt.strftime("%d/%m/%Y %H:%M")
                            else:
                                formatted = start
                        except:
                            formatted = start
                        
                        html_link = result_data.get("html_link", "")
                        tool_response_parts.append(f"✅ Evento creado exitosamente:\n\n**{summary}**\n📅 {formatted}\n\n🔗 [Ver en Google Calendar]({html_link})")
                    
                    elif "event_id" in result_data and "summary" in result_data:
                        # Event updated
                        summary = result_data.get("summary", "Evento")
                        html_link = result_data.get("html_link", "")
                        tool_response_parts.append(f"✅ Evento actualizado exitosamente:\n\n**{summary}**\n\n🔗 [Ver en Google Calendar]({html_link})")
                
                # Email tool: format emails for response
                elif tool_used == "email" and isinstance(result_data, dict) and result_data.get("success"):
                    # Check if it's a SEND or LIST operation
                    if "message_id" in result_data:
                        # Email sent successfully
                        to = result_data.get("to", "")
                        subject = result_data.get("subject", "")
                        tool_response_parts.append(f"✅ Correo enviado exitosamente:\n\n**Para:** {to}\n**Asunto:** {subject}")
                    
                    elif "messages" in result_data:
                        # List emails
                        messages = result_data.get("messages", [])
                        if messages:
                            email_list = []
                            # Try to respect requested limit if provided in result_data or show up to 10
                            display_limit = min(result_data.get("count", len(messages)), 10)
                            for msg in messages[:display_limit]:
                                sender = msg.get("from", "Desconocido")
                                subject = msg.get("subject", "Sin asunto")
                                date = msg.get("date", "")
                                snippet = msg.get("snippet", "")
                                email_list.append(f"• **De:** {sender}\n  **Asunto:** {subject}\n  **Fecha:** {date}\n  _{snippet[:100]}..._")
                            
                            count = result_data.get("count", len(messages))
                            tool_response_parts.append(f"📧 Tienes {count} correos recientes:\n\n" + "\n\n".join(email_list))

        # After processing tool results, if we collected parts, join into a single tool_response
        if tool_response_parts:
            tool_response = "\n\n".join(tool_response_parts)

        # Quick intent check: if the user is asking about what documents/files are uploaded,
        # return the listing/count directly (no need to call RAG).
        try:
            msg_l = (message.message or "").lower()
            looks_for_docs = False
            if "document" in msg_l or "archivo" in msg_l or "fichero" in msg_l:
                if any(k in msg_l for k in ["cuánt", "cuantos", "qué documentos", "que documentos", "dime que documentos", "qué archivos", "que archivos", "qué ficheros", "que ficheros"]):
                    looks_for_docs = True

            if looks_for_docs:
                try:
                    up_dir = settings.UPLOAD_DIR
                    files = []
                    if up_dir and os.path.isdir(up_dir):
                        for fn in os.listdir(up_dir):
                            fp = os.path.join(up_dir, fn)
                            if os.path.isfile(fp):
                                files.append(fn)
                    if files:
                        response_text = f"Hay {len(files)} documentos subidos: {', '.join(files)}"
                    else:
                        response_text = "No hay documentos subidos."

                    res = ChatResponse(
                        response=response_text,
                        conversation_id=message.conversation_id or f"conv_{datetime.utcnow().timestamp()}",
                        timestamp=datetime.utcnow().isoformat(),
                        plan=[s.model_dump() for s in plan.subtasks],
                        execution=exec_results,
                        evaluation=evaluation,
                        sources=[],
                    )
                    return res
                except Exception:
                    # If listing fails, continue to RAG flow as a fallback
                    logger.debug("Failed to list upload dir during docs-intent handling")
        except Exception:
            # Intent detection should never break the chat flow
            logger.debug("Docs-intent detection failed; proceeding with normal flow")

        # 5) Intelligent intent detection to determine if we should query RAG
        intent_detector = get_intent_detector()
        intent_result = intent_detector.detect_intent(message.message)
        
        logger.info(f"Intent detection: {intent_result['intent']} (confidence: {intent_result['confidence']}, needs_rag: {intent_result['needs_rag']})")
        logger.debug(f"Intent reasoning: {intent_result['reasoning']}")
        
        should_query_rag = intent_result['needs_rag']
        
        sources = None
        rag_context_text = None
        
        # Try to enrich with RAG sources if relevant
        if should_query_rag:
            try:
                from app.rag.query import semantic_search
                
                # Detect if user mentions a specific file name
                file_filter = None
                file_mention = re.search(r'([\w-]+\.(?:pdf|txt|docx?|xlsx?|csv|md))', message.message, re.IGNORECASE)
                if file_mention:
                    mentioned_file = file_mention.group(1)
                    file_id_stem = mentioned_file.rsplit('.', 1)[0]  # "CV.pdf" -> "CV"
                    logger.info(f"📄 Detected file mention in chat: {mentioned_file} (file_id: {file_id_stem})")
                    # Filter by source (exact match) OR file_id (stem)
                    file_filter = {"$or": [
                        {"file_id": {"$eq": file_id_stem}},
                        {"source": {"$eq": mentioned_file}}
                    ]}
                
                logger.info(f"RAG query for: {message.message[:100]}")
                
                try:
                    rag_results = semantic_search(
                        query=message.message,
                        top_k=5,
                        collection_name="servibot_docs",
                        filter_metadata=file_filter
                    )
                    
                    if rag_results:
                        # Transform to include snippets and metadata
                        sources = []
                        for result in rag_results:
                            doc_text = result.get("document", "")
                            metadata = result.get("metadata", {})
                            distance = result.get("distance", 1.0)
                            
                            source_name = metadata.get("source", metadata.get("file_id", "documento"))
                            chunk_index = metadata.get("chunk_index", 0)
                            
                            # Only include if document text exists
                            if doc_text:
                                snippet = doc_text[:400].strip() + ("..." if len(doc_text) > 400 else "")
                                sources.append({
                                    "filename": source_name,
                                    "snippet": snippet,
                                    "chunk_index": chunk_index,
                                    "distance": round(distance, 3)
                                })
                        
                        logger.info(f"RAG returned {len(sources)} results with snippets")
                        
                        # Extract text snippets for context
                        snippets = []
                        for i, src in enumerate(sources[:3], 1):  # Top 3
                            snippets.append(f"[Fragmento {i} de {src['filename']}]\n{src['snippet']}")
                        
                        if snippets:
                            rag_context_text = "\n\n---\n\n".join(snippets)
                    else:
                        logger.info("RAG query returned no results")
                        sources = []
                        
                except Exception as rag_err:
                    logger.info(f"RAG query error (likely no documents): {rag_err}")
                    sources = []
                    
            except Exception as e:
                logger.warning(f"RAG enrichment failed: {e}")
                sources = []
        else:
            logger.info(f"RAG skipped - query not document-related")

        # 6) Generate response using LM with full context
        # ALWAYS use the LM to generate natural, contextual responses
        response_text = None
        # Server-side relative date resolution to avoid LM arithmetic errors
        def _parse_relative_days(text: str):
            t = (text or "").lower()
            t = t.replace("á", "a")
            if "hoy" in t:
                return 0
            if "pasado mañana" in t or "pasado mañana" in t:
                return 2
            if "mañana" in t or "manana" in t:
                return 1
            m = re.search(r"dentro de\s+(\d+)\s*d[ií]as", t)
            if not m:
                m = re.search(r"en\s+(\d+)\s*d[ií]as", t)
            if m:
                try:
                    return int(m.group(1))
                except Exception:
                    return None
            return None

        computed_date_text = None
        rel_days = _parse_relative_days(message.message)
        if rel_days is not None:
            now_local = datetime.now()
            target = now_local + timedelta(days=rel_days)
            month_map = {
                1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
                7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
            }
            computed_date_text = f"Fecha calculada (servidor): {target.day} de {month_map.get(target.month)} de {target.year}"
        
        try:
            from app.llm.local_client import generate_response_with_context
            
            # Get current date for temporal context (force Spanish month names)
            now = datetime.now()
            month_map = {
                1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
                7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
            }
            current_date = f"{now.day} de {month_map.get(now.month, now.strftime('%B'))} de {now.year}"
            
            # Combine any tool response with computed date context (if present)
            tool_results_combined = None
            if tool_response and computed_date_text:
                tool_results_combined = f"{tool_response}\n\n{computed_date_text}"
            elif computed_date_text:
                tool_results_combined = computed_date_text
            else:
                tool_results_combined = tool_response

            # Generate response with full context
            response_text = generate_response_with_context(
                user_message=message.message,
                tool_results=tool_results_combined,
                rag_context=rag_context_text,
                current_date=current_date,
                user_info=user_info,
                max_tokens=200,
                temperature=0.3  # Slightly creative but still factual
            )
            
            logger.info(f"✅ LM generated response: {response_text[:100]}...")
            
            # Store LLM response in execution context for PDF generation
            execution_context["llm_response"] = response_text
            
        except Exception as e:
            logger.warning(f"LM generation failed: {e}")
            # Fallback logic if LM fails
            if tool_response:
                response_text = tool_response
            elif rag_context_text:
                response_text = f"Encontré información en los documentos:\n\n{rag_context_text[:1000]}"
            else:
                response_text = "He procesado tu solicitud. Por favor, proporciona más detalles si necesitas ayuda adicional."
        
        # Legacy RAG processing (only used if LM generation failed and we need sources)
        # Sources are now a list of dicts with {filename, snippet, chunk_index, distance}
        # No need to normalize - keep as is for frontend display
        if not sources:
            sources = []

        # Check if a file was generated during execution
        generated_file = None
        logger.info(f"🔍 Checking execution results for generated files...")
        logger.info(f"   Total results: {len(exec_results.get('results', []))}")
        
        for idx, result in enumerate(exec_results.get("results", [])):
            result_data = result.get("result", {})
            tool_used = result.get("tool", "unknown")
            logger.info(f"   Result {idx}: tool={tool_used}, type={type(result_data)}, keys={list(result_data.keys()) if isinstance(result_data, dict) else 'N/A'}")
            
            # document_generator returns {"success": True, "filename": ...}
            if isinstance(result_data, dict) and result_data.get("success") and "filename" in result_data:
                # File was generated, prepare download URL
                filename = result_data["filename"]
                file_format = result_data.get("format", "pdf").upper()
                generated_file = {
                    "filename": filename,
                    "download_url": f"/api/generate/download/{filename}",
                    "message": f"Archivo {file_format} generado correctamente"
                }
                # Add info to response
                response_text += f"\n\n✅ Archivo {file_format} generado: {filename}\n📥 La descarga comenzará automáticamente"
                logger.info(f"✅ Generated file detected: {filename}")
                break
        
        if not generated_file:
            logger.warning("⚠️ No generated file found in execution results")

        res = ChatResponse(
            response=response_text,
            conversation_id=message.conversation_id or f"conv_{datetime.utcnow().timestamp()}",
            timestamp=datetime.utcnow().isoformat(),
            plan=[s.model_dump() for s in plan.subtasks],
            execution=exec_results,
            evaluation=evaluation,
            sources=sources,
        )
        
        # Add generated_file to response if available (extend model if needed)
        if generated_file:
            res.generated_file = generated_file
        
        return res

    except Exception as e:
        logger.exception("Error processing chat message")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.get("/chat/history/{conversation_id}")
async def get_chat_history(conversation_id: str):
    """
    Retrieve chat history for a conversation.
    
    Args:
        conversation_id: Unique conversation identifier
        
    Returns:
        List of messages in the conversation
    """
    # TODO: Implement conversation history retrieval from database
    return {
        "conversation_id": conversation_id,
        "messages": [],
        "message": "History retrieval will be implemented soon"
    }


@router.post("/chat/stream")
async def chat_stream(message: ChatMessage):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    Emits events for plan, execution steps, and final response.
    
    Args:
        message: Chat message with user input
        
    Returns:
        StreamingResponse with text/event-stream content
    """
    from fastapi.responses import StreamingResponse
    import json
    import asyncio
    
    async def event_generator():
        """Generate SSE events for chat stream."""
        try:
            # Step 1: Generate plan
            yield f"event: plan\ndata: {{\"type\": \"plan\", \"status\": \"generating\"}}\n\n"
            await asyncio.sleep(0.1)
            
            plan = planner.generate_plan(message.message, message.context)
            plan_data = {
                "type": "plan",
                "status": "generated",
                "subtasks": [s.model_dump() for s in plan.subtasks]
            }
            yield f"event: plan\ndata: {json.dumps(plan_data)}\n\n"
            
            # Step 2: Execute steps one by one and emit progress
            for subtask in plan.subtasks:
                step_start = {
                    "type": "step",
                    "step": subtask.step,
                    "status": "running",
                    "action": subtask.action,
                    "tool": subtask.tool
                }
                yield f"event: step\ndata: {json.dumps(step_start)}\n\n"
                await asyncio.sleep(0.2)  # Simulate processing
                
                # Complete step
                step_done = {
                    "type": "step",
                    "step": subtask.step,
                    "status": "completed",
                    "action": subtask.action
                }
                yield f"event: step\ndata: {json.dumps(step_done)}\n\n"
            
            # Step 3: Final execution (simplified - actual execution happens in real impl)
            exec_results = await executor.execute_plan(plan, context=message.context)
            
            # Step 4: Evaluation
            evaluation = evaluator.evaluate_results(exec_results)
            
            # Step 5: Final response
            response_data = {
                "type": "response",
                "status": "completed",
                "message": "Tarea completada exitosamente",
                "execution": exec_results,
                "evaluation": evaluation
            }
            yield f"event: response\ndata: {json.dumps(response_data)}\n\n"
            
            # Done signal
            yield "event: done\ndata: {\"type\": \"done\"}\n\n"
            
        except Exception as e:
            logger.exception("Error in chat stream")
            error_data = {
                "type": "error",
                "message": str(e)
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
