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
                self.register_tool("notes", notes_mock.create_note)
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
