"""
Agent Planner Module
Generates execution plans from user objectives.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class SubTask(BaseModel):
    """Represents a subtask in the execution plan."""
    step: int
    action: str
    tool: Optional[str] = None
    estimated_time_minutes: int = 1
    requires_confirmation: bool = False
    dependencies: List[int] = []
    success_criteria: str = ""


class ExecutionPlan(BaseModel):
    """Complete execution plan for a user objective."""
    objective: str
    subtasks: List[SubTask]
    total_estimated_time: int
    requires_user_confirmation: bool
    risk_level: str = "low"  # low, medium, high


class Planner:
    """
    Agent planner that generates structured execution plans.
    Uses LLM to break down user objectives into actionable subtasks.
    """
    
    def __init__(self, llm_client=None):
        """
        Initialize the planner.
        
        Args:
            llm_client: Language model client for generating plans
        """
        self.llm_client = llm_client
        logger.info("Planner initialized")
    
    def generate_plan(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ExecutionPlan:
        """
        Generate an execution plan from a user objective.
        
        Args:
            objective: User's goal or request
            context: Additional context (calendar, preferences, documents)
            
        Returns:
            ExecutionPlan with structured subtasks
        """
        logger.info(f"Generating plan for objective: {objective}")
        
        # Detect query type WITH PRIORITY ORDER
        obj_lower = objective.lower()
        
        # PRIORITY 1: Email SEND operation (highest priority)
        is_email_send = any(kw in obj_lower for kw in ["enviar", "envia", "envía", "mandar", "manda", "send"]) and \
                        any(kw in obj_lower for kw in ["correo", "email", "mensaje", "mail"])
        
        # Calendar query: asking about events or schedule
        is_calendar_query = any(kw in obj_lower for kw in [
            "evento", "eventos", "calendario", "calendar", "agenda", "reunión", "reuniones",
            "meeting", "cita", "appointment", "próximo", "próximos", "siguiente", "next",
            "horario", "schedule", "cuándo tengo", "cuando tengo", "what's on my"
        ]) and not is_email_send  # Don't override email send
        
        # Email query: asking about messages, inbox, OR sending emails
        is_email_query = any(kw in obj_lower for kw in [
            "email", "correo", "correos", "mensaje", "mensajes", "inbox", "bandeja",
            "mail", "gmail", "recibido", "enviado", "sent", "received"
        ]) or is_email_send
        
        # Metadata query: asking ABOUT documents (how many, which files, etc.)
        is_metadata_query = False
        if any(word in obj_lower for word in ["document", "archivo", "fichero", "file"]):
            if any(kw in obj_lower for kw in ["cuánt", "cuantos", "qué documentos", "que documentos", "dime que", "qué archivos", "que archivos", "listar", "mostrar", "list"]):
                is_metadata_query = True
        
        # File generation: user wants to create/export something
        is_file_generation = any(kw in obj_lower for kw in [
            "generar", "crear", "exportar", "hacer", "generate", "create", "export",
            "pdf", "excel", "documento", "archivo", "reporte", "informe"
        ])
        
        # Information query: user asking questions about content
        is_info_query = any(kw in obj_lower for kw in [
            "qué", "que", "cuál", "cual", "cómo", "como", "quién", "quien", "dónde", "donde",
            "cuándo", "cuando", "por qué", "porque", "dame", "dime", "explica", "muestra",
            "what", "which", "how", "who", "where", "when", "why", "tell", "show", "explain"
        ]) and not is_metadata_query and not is_calendar_query and not is_email_query
        
        # Generate appropriate plan based on query type
        if is_calendar_query:
            # Calendar plan: list upcoming events
            subtasks = [
                SubTask(
                    step=1,
                    action="List upcoming calendar events",
                    tool="calendar",
                    estimated_time_minutes=1,
                    requires_confirmation=False,
                    success_criteria="Calendar events retrieved"
                )
            ]
        elif is_email_query:
            # Email plan: detect if it's SEND or LIST
            is_send = any(kw in obj_lower for kw in ["enviar", "envia", "envía", "mandar", "manda", "send"])
            
            if is_send:
                # Send email operation
                subtasks = [
                    SubTask(
                        step=1,
                        action="Send email with extracted parameters",
                        tool="email",
                        estimated_time_minutes=1,
                        requires_confirmation=False,
                        success_criteria="Email sent successfully"
                    )
                ]
            else:
                # List emails operation
                subtasks = [
                    SubTask(
                        step=1,
                        action="List recent emails from inbox",
                        tool="email",
                        estimated_time_minutes=1,
                        requires_confirmation=False,
                        success_criteria="Email messages retrieved"
                    )
                ]
        elif is_metadata_query:
            # Simple plan for listing files
            subtasks = [
                SubTask(
                    step=1,
                    action="List available documents from storage",
                    tool="file_system",
                    estimated_time_minutes=1,
                    requires_confirmation=False,
                    success_criteria="Document list retrieved"
                )
            ]
        elif is_file_generation:
            # Plan for generating files (PDF, Excel, etc.)
            subtasks = [
                SubTask(
                    step=1,
                    action="Gather content from knowledge base",
                    tool="rag_query",
                    estimated_time_minutes=1,
                    requires_confirmation=False,
                    success_criteria="Content retrieved"
                ),
                SubTask(
                    step=2,
                    action="Generate requested file",
                    tool="file_writer",
                    estimated_time_minutes=2,
                    requires_confirmation=False,
                    dependencies=[1],
                    success_criteria="File generated and downloadable"
                )
            ]
        else:
            # Default plan: Query knowledge base and respond
            subtasks = [
                SubTask(
                    step=1,
                    action="Search relevant information in uploaded documents",
                    tool="rag_query",
                    estimated_time_minutes=1,
                    requires_confirmation=False,
                    success_criteria="Relevant information found"
                ),
                SubTask(
                    step=2,
                    action="Analyze and formulate response",
                    tool="llm_reasoning",
                    estimated_time_minutes=1,
                    requires_confirmation=False,
                    dependencies=[1],
                    success_criteria="Clear answer provided"
                )
            ]
        
        plan = ExecutionPlan(
            objective=objective,
            subtasks=subtasks,
            total_estimated_time=sum(t.estimated_time_minutes for t in subtasks),
            requires_user_confirmation=any(t.requires_confirmation for t in subtasks),
            risk_level="low"
        )
        
        logger.info(f"Plan generated with {len(subtasks)} subtasks")
        return plan
    
    def _build_planner_prompt(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build the prompt for the LLM planner.
        
        Args:
            objective: User's objective
            context: Additional context
            
        Returns:
            Formatted prompt string
        """
        context_summary = ""
        if context:
            context_summary = f"\n\nAvailable context:\n{context}"
        
        prompt = f"""You are a planner for the SERVIBOT autonomous agent.

Your task: Generate a structured execution plan for the following objective.

Objective: "{objective}"{context_summary}

Instructions:
1. Break down the objective into specific, actionable subtasks
2. For each subtask, specify:
   - Action description
   - Recommended tool (calendar_tool, email_tool, notes_tool, file_writer, rag_query, or none)
   - Estimated time in minutes
   - Whether it requires user confirmation
   - Success criteria
3. Identify dependencies between subtasks
4. Assess overall risk level (low/medium/high)

Available tools:
- calendar: List upcoming events or create new calendar entries in Google Calendar
- email: List/read emails or send new messages via Gmail
- notes_tool: Create notes in Notion/Todoist
- file_writer: Generate PDF or Excel files
- rag_query: Search knowledge base for context

Output format: JSON with structure matching ExecutionPlan model.
"""
        return prompt


# Global planner instance
planner = Planner()
