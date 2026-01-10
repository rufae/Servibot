"""
Tests for Agent Executor module
"""
import pytest
from app.agent.executor import executor, Executor, ExecutionResult
from app.agent.planner import ExecutionPlan, SubTask


class TestExecutorBasic:
    """Basic tests for executor functionality."""
    
    def test_executor_instance_exists(self):
        """Test that executor singleton exists."""
        assert executor is not None
        assert isinstance(executor, Executor)
    
    def test_executor_has_tools(self):
        """Test that executor has tools registered."""
        assert hasattr(executor, 'tools')
        assert isinstance(executor.tools, dict)
    
    @pytest.mark.asyncio
    async def test_execute_plan_returns_dict(self):
        """Test that execute_plan returns a dictionary."""
        plan = ExecutionPlan(
            objective="Test objective",
            subtasks=[
                SubTask(
                    step=1,
                    action="Test action",
                    tool="file_writer",
                    requires_confirmation=False
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=False
        )
        
        result = await executor.execute_plan(plan)
        
        assert isinstance(result, dict)
        assert "objective" in result
        assert "results" in result


class TestExecutorSubtaskExecution:
    """Tests for individual subtask execution."""
    
    @pytest.mark.asyncio
    async def test_execute_simple_subtask(self):
        """Test execution of a simple subtask."""
        plan = ExecutionPlan(
            objective="Simple test",
            subtasks=[
                SubTask(
                    step=1,
                    action="Create a test file",
                    tool="file_writer",
                    requires_confirmation=False
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=False
        )
        
        result = await executor.execute_plan(plan)
        
        assert result["total_steps"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["step"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_multiple_subtasks(self):
        """Test execution of multiple subtasks."""
        plan = ExecutionPlan(
            objective="Multiple tasks",
            subtasks=[
                SubTask(step=1, action="Task 1", tool="file_writer", requires_confirmation=False),
                SubTask(step=2, action="Task 2", tool="notes", requires_confirmation=False),
                SubTask(step=3, action="Task 3", tool="email", requires_confirmation=False),
            ],
            total_estimated_time=3,
            requires_user_confirmation=False
        )
        
        result = await executor.execute_plan(plan)
        
        assert result["total_steps"] == 3
        assert len(result["results"]) == 3


class TestExecutorConfirmations:
    """Tests for confirmation handling."""
    
    @pytest.mark.asyncio
    async def test_task_requires_confirmation_pending(self):
        """Test that task requiring confirmation stays pending without confirmation."""
        plan = ExecutionPlan(
            objective="Test confirmation",
            subtasks=[
                SubTask(
                    step=1,
                    action="Sensitive action",
                    tool="email",
                    requires_confirmation=True
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=True
        )
        
        # Execute without confirmations
        result = await executor.execute_plan(plan)
        
        assert result["results"][0]["status"] == "pending"
        assert "confirmation" in result["results"][0]["error"].lower()
    
    @pytest.mark.asyncio
    async def test_task_with_confirmation_approved(self):
        """Test task execution when confirmation is approved."""
        plan = ExecutionPlan(
            objective="Test confirmation",
            subtasks=[
                SubTask(
                    step=1,
                    action="Confirmed action",
                    tool="email",
                    requires_confirmation=True
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=True
        )
        
        confirmations = {1: True}
        result = await executor.execute_plan(plan, user_confirmations=confirmations)
        
        assert result["results"][0]["status"] in ["success", "failed"]
        assert result["results"][0]["status"] != "pending"
    
    @pytest.mark.asyncio
    async def test_task_with_confirmation_declined(self):
        """Test task skipping when confirmation is declined."""
        plan = ExecutionPlan(
            objective="Test decline",
            subtasks=[
                SubTask(
                    step=1,
                    action="Declined action",
                    tool="email",
                    requires_confirmation=True
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=True
        )
        
        confirmations = {1: False}
        result = await executor.execute_plan(plan, user_confirmations=confirmations)
        
        assert result["results"][0]["status"] == "skipped"


class TestExecutorContext:
    """Tests for context passing to executor."""
    
    @pytest.mark.asyncio
    async def test_execute_with_context(self):
        """Test executor receives and uses context."""
        plan = ExecutionPlan(
            objective="Test with context",
            subtasks=[
                SubTask(
                    step=1,
                    action="Use context",
                    tool="file_writer",
                    requires_confirmation=False
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=False
        )
        
        context = {
            "user_message": "Generate report",
            "rag_summary": "Test RAG content"
        }
        
        result = await executor.execute_plan(plan, context=context)
        
        assert result["results"][0]["step"] == 1
    
    @pytest.mark.asyncio
    async def test_execute_without_context(self):
        """Test executor works without context."""
        plan = ExecutionPlan(
            objective="Test no context",
            subtasks=[
                SubTask(
                    step=1,
                    action="Simple action",
                    tool="file_writer",
                    requires_confirmation=False
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=False
        )
        
        result = await executor.execute_plan(plan, context=None)
        
        assert len(result["results"]) == 1


class TestExecutorToolRouting:
    """Tests for tool routing and execution."""
    
    @pytest.mark.asyncio
    async def test_file_writer_tool_routing(self):
        """Test that file_writer tool is routed correctly."""
        plan = ExecutionPlan(
            objective="Test file writer",
            subtasks=[
                SubTask(
                    step=1,
                    action="Generate PDF",
                    tool="file_writer",
                    requires_confirmation=False
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=False
        )
        
        result = await executor.execute_plan(plan)
        
        assert result["results"][0]["tool_used"] == "file_writer"
    
    @pytest.mark.asyncio
    async def test_unknown_tool_handling(self):
        """Test handling of unknown/unmapped tools."""
        plan = ExecutionPlan(
            objective="Test unknown tool",
            subtasks=[
                SubTask(
                    step=1,
                    action="Use unknown tool",
                    tool="unknown_tool_xyz",
                    requires_confirmation=False
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=False
        )
        
        result = await executor.execute_plan(plan)
        
        # Should still execute (simulated) or handle gracefully
        assert result["results"][0]["status"] in ["success", "failed"]


class TestExecutorResults:
    """Tests for execution results structure."""
    
    @pytest.mark.asyncio
    async def test_result_has_required_fields(self):
        """Test that execution results have all required fields."""
        plan = ExecutionPlan(
            objective="Test result fields",
            subtasks=[
                SubTask(
                    step=1,
                    action="Test action",
                    tool="file_writer",
                    requires_confirmation=False
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=False
        )
        
        result = await executor.execute_plan(plan)
        
        assert "objective" in result
        assert "total_steps" in result
        assert "completed_steps" in result
        assert "failed_steps" in result
        assert "results" in result
        
        task_result = result["results"][0]
        assert "step" in task_result
        assert "status" in task_result
        assert "tool_used" in task_result
    
    @pytest.mark.asyncio
    async def test_completed_steps_count(self):
        """Test that completed_steps count is accurate."""
        plan = ExecutionPlan(
            objective="Count test",
            subtasks=[
                SubTask(step=1, action="Task 1", tool="file_writer", requires_confirmation=False),
                SubTask(step=2, action="Task 2", tool="notes", requires_confirmation=False),
            ],
            total_estimated_time=2,
            requires_user_confirmation=False
        )
        
        result = await executor.execute_plan(plan)
        
        successful = [r for r in result["results"] if r["status"] == "success"]
        assert result["completed_steps"] == len(successful)


class TestExecutorErrorHandling:
    """Tests for error handling during execution."""
    
    @pytest.mark.asyncio
    async def test_execution_with_error(self):
        """Test that errors are captured in results."""
        plan = ExecutionPlan(
            objective="Test error",
            subtasks=[
                SubTask(
                    step=1,
                    action="This might fail",
                    tool="file_writer",
                    requires_confirmation=False
                )
            ],
            total_estimated_time=1,
            requires_user_confirmation=False
        )
        
        result = await executor.execute_plan(plan)
        
        # Should complete without raising exception
        assert "results" in result
        assert len(result["results"]) == 1


class TestExecutorToolRegistration:
    """Tests for tool registration functionality."""
    
    def test_register_tool(self):
        """Test registering a new tool."""
        def dummy_tool(action: str):
            return {"status": "success", "message": action}
        
        initial_count = len(executor.tools)
        executor.register_tool("test_tool", dummy_tool)
        
        assert len(executor.tools) == initial_count + 1
        assert "test_tool" in executor.tools
        
        # Cleanup
        del executor.tools["test_tool"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
