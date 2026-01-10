"""
Chat API Endpoint
Handles user chat interactions with the ServiBot agent.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import logging

from app.agent.planner import planner
from app.agent.executor import executor
from app.agent.evaluator import evaluator
from app.core.config import settings
from app.llm.local_client import summarize_texts
import os

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message request model."""
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


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


@router.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Main chat endpoint that processes user messages through the agent.

    Flow implemented:
    1. Planner generates an ExecutionPlan from the user message.
    2. Executor runs the plan. Using "confirmación automática": all steps are auto-confirmed.
    3. Evaluator assesses the execution results.
    4. Return structured response with plan, execution results and evaluation.
    """
    try:
        logger.info(f"Received chat message: {message.message[:50]}...")

        # 1) Generate plan
        plan = planner.generate_plan(message.message, message.context)

        # 2) Build auto-confirmations (confirm all steps)
        user_confirmations: Dict[int, bool] = {s.step: True for s in plan.subtasks}

        # 3) Prepare context for executor (will include RAG results if available)
        execution_context = {
            "user_message": message.message,
            "original_context": message.context or {}
        }

        # 3) Execute the plan
        exec_results = await executor.execute_plan(plan, user_confirmations=user_confirmations, context=execution_context)

        # 4) Evaluate results
        evaluation = evaluator.evaluate_results(exec_results)

        # Check if executor returned data from calendar/email tools
        tool_response = None
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
                            tool_response = f"📅 Tienes {count} eventos próximos:\n\n" + "\n".join(event_list)
                    
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
                        tool_response = f"✅ Evento creado exitosamente:\n\n**{summary}**\n📅 {formatted}\n\n🔗 [Ver en Google Calendar]({html_link})"
                    
                    elif "event_id" in result_data and "summary" in result_data:
                        # Event updated
                        summary = result_data.get("summary", "Evento")
                        html_link = result_data.get("html_link", "")
                        tool_response = f"✅ Evento actualizado exitosamente:\n\n**{summary}**\n\n🔗 [Ver en Google Calendar]({html_link})"
                
                # Email tool: format emails for response
                elif tool_used == "email" and isinstance(result_data, dict) and result_data.get("success"):
                    # Check if it's a SEND or LIST operation
                    if "message_id" in result_data:
                        # Email sent successfully
                        to = result_data.get("to", "")
                        subject = result_data.get("subject", "")
                        tool_response = f"✅ Correo enviado exitosamente:\n\n**Para:** {to}\n**Asunto:** {subject}"
                    
                    elif "messages" in result_data:
                        # List emails
                        messages = result_data.get("messages", [])
                        if messages:
                            email_list = []
                            for msg in messages[:10]:  # Limit to 10 emails
                                sender = msg.get("from", "Desconocido")
                                subject = msg.get("subject", "Sin asunto")
                                date = msg.get("date", "")
                                snippet = msg.get("snippet", "")
                                email_list.append(f"• **De:** {sender}\n  **Asunto:** {subject}\n  **Fecha:** {date}\n  _{snippet[:100]}..._")
                            
                            count = result_data.get("count", len(messages))
                            tool_response = f"📧 Tienes {count} correos recientes:\n\n" + "\n\n".join(email_list)

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

        # 5) Try to enrich with RAG sources - ALWAYS query ChromaDB if documents are indexed
        sources = None
        try:
            from app.rag.query import semantic_search
            
            # ALWAYS try RAG query to leverage uploaded documents
            logger.info(f"Querying RAG for: {message.message[:100]}")
            
            try:
                rag_results = semantic_search(
                    query=message.message,
                    top_k=5,
                    collection_name="servibot_docs"
                )
                
                if rag_results:
                    sources = rag_results
                    logger.info(f"RAG returned {len(sources)} results")
                else:
                    logger.info("RAG query returned no results")
                    
            except Exception as rag_err:
                # Handle errors gracefully (e.g., no collection exists)
                logger.info(f"RAG query error (likely no documents): {rag_err}")
                sources = None
                
        except Exception as e:
            # If RAG dependencies are missing or an error occurs, log and continue without sources
            logger.warning(f"RAG enrichment failed: {e}")
            sources = None

        # 6) Prepare response
        response_text = None
        # If we have RAG sources, try to present them usefully.
        if sources and len(sources) > 0:
            try:
                items = [s for s in sources if s and isinstance(s, dict)]

                # Deduplicate by file_id/source
                unique = {}
                for s in items:
                    md = s.get("metadata") or {}
                    fid = md.get("file_id") or md.get("source") or None
                    key = fid or (s.get("document")[:50] if s.get("document") else None)
                    if key and key not in unique:
                        unique[key] = s

                # Heuristic: if the user asked specifically about documents/files,
                # return the uploaded filenames / count instead of a fragment summary.
                msg_l = (message.message or "").lower()
                looks_for_docs = False
                if "document" in msg_l or "archivo" in msg_l or "fichero" in msg_l:
                    if any(k in msg_l for k in ["cuánt", "cuantos", "qué documentos", "que documentos", "dime que documentos", "qué archivos", "que archivos", "qué ficheros", "que ficheros"]):
                        looks_for_docs = True

                if looks_for_docs:
                    # Prefer listing actual uploaded files from the upload directory
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
                            # Fallback to unique file ids from the RAG results
                            uf = list(unique.keys())
                            response_text = f"Hay {len(uf)} documentos (estimado): {', '.join(uf)}"
                    except Exception as e:
                        logger.debug(f"Error listing upload dir: {e}")
                        uf = list(unique.keys())
                        response_text = f"Hay {len(uf)} documentos (estimado): {', '.join(uf)}"
                else:
                    # Default behavior: summarize top-K fragments, but report unique files instead of raw fragment count
                    # Sort by distance ascending if present
                    sorted_items = sorted(unique.values(), key=lambda x: x.get("distance") if x.get("distance") is not None else float("inf"))
                    TOP_K_SUMMARY = min(len(sorted_items), 5)
                    top_items = sorted_items[:TOP_K_SUMMARY]
                    texts = [t.get("document") for t in top_items if t.get("document")]

                    summary = None
                    if texts and settings.LM_USE_LOCAL_LM:
                        try:
                            # Create a prompt that uses the RAG context to answer the user query
                            context = "\n\n---\n\n".join([f"Fragmento {i+1}:\n{t}" for i, t in enumerate(texts)])
                            summary_prompt = f"""Basándote en la siguiente información de los documentos, responde a la pregunta del usuario de forma clara y concisa.

Pregunta del usuario: {message.message}

Información de los documentos:
{context}

Respuesta (directa y basada en la información proporcionada):"""
                            
                            summary = summarize_texts([summary_prompt], max_tokens=512)
                            logger.info(f"Generated RAG-based answer via local LM: {summary[:100]}...")
                        except Exception as e:
                            logger.warning(f"Local LM summarization failed: {e}")

                    if not summary and texts:
                        # Fallback: just show concatenated fragments with context
                        cleaned = []
                        for i, t in enumerate(texts):
                            if not t:
                                continue
                            s = " ".join(t.split())
                            cleaned.append(f"📄 Fragmento {i+1}:\n{s[:400]}")
                        summary = "\n\n".join(cleaned)
                        logger.info("Using fallback concatenation for summary")

                    source_names = [((s.get("metadata") or {}).get("source") or ((s.get("metadata") or {}).get("file_id"))) for s in top_items]
                    source_names = [n for n in source_names if n]
                    
                    if summary:
                        response_text = summary
                    else:
                        # If we couldn't generate any summary, show a generic message with source count
                        response_text = f"Encontré {len(unique)} documentos relacionados con tu consulta, pero no pude extraer información específica."
                    
                    # Normalize sources to a simple list of filenames for the frontend
                    sources = source_names
                    
                    # Add RAG content to execution context for tools (like file_writer)
                    execution_context["rag_summary"] = summary
                    execution_context["rag_sources"] = source_names
                    execution_context["rag_texts"] = texts[:3]  # Top 3 fragments
            except Exception as e:
                logger.exception(f"Error building summary from sources: {e}")
                response_text = None
        
        # Fallback if no response was generated
        if not response_text:
            # Priority 1: Check if we have tool response from calendar/email
            if tool_response:
                response_text = tool_response
                sources = []  # Clear sources when using tools
            else:
                response_text = "He procesado tu solicitud. Por favor, proporciona más detalles o sube documentos para poder ayudarte mejor."
        else:
            # If RAG generated a response but we also have tool_response, prefer tool_response
            if tool_response:
                response_text = tool_response
                sources = []  # Clear sources when using tools
        # Ensure sources is a list of simple filenames (strings) or empty list
        if sources and isinstance(sources, list):
            # If sources contains dicts (old shape), extract filenames
            normalized = []
            for s in sources:
                if isinstance(s, str):
                    normalized.append(s)
                elif isinstance(s, dict):
                    md = s.get("metadata") or {}
                    fn = md.get("source") or md.get("file_id") or None
                    if fn:
                        normalized.append(fn)
            sources = list(dict.fromkeys(normalized))
        else:
            sources = []

        # Check if a file was generated during execution
        generated_file = None
        for result in exec_results.get("results", []):
            result_data = result.get("result", {})
            if isinstance(result_data, dict) and result_data.get("status") == "success" and "filename" in result_data:
                # File was generated, prepare download URL
                filename = result_data["filename"]
                generated_file = {
                    "filename": filename,
                    "download_url": f"/api/generate/download/{filename}",
                    "message": result_data.get("message", f"Archivo generado: {filename}")
                }
                # Add info to response
                response_text += f"\n\n✅ {generated_file['message']}\n📥 Descarga disponible"
                break

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
