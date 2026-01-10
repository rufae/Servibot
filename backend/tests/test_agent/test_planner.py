"""
Tests for Agent Planner module
"""
import pytest
from app.agent.planner import planner, Planner, ExecutionPlan, SubTask


class TestPlannerBasic:
    """Basic tests for planner functionality."""
    
    def test_planner_instance_exists(self):
        """Test that planner singleton exists."""
        assert planner is not None
        assert isinstance(planner, Planner)
    
    def test_generate_plan_returns_execution_plan(self):
        """Test that generate_plan returns ExecutionPlan object."""
        plan = planner.generate_plan("Create a note about testing")
        
        assert isinstance(plan, ExecutionPlan)
        assert hasattr(plan, 'objective')
        assert hasattr(plan, 'subtasks')
    
    def test_plan_has_subtasks(self):
        """Test that generated plan contains subtasks."""
        plan = planner.generate_plan("Send an email to john@example.com")
        
        assert len(plan.subtasks) > 0
        assert all(isinstance(task, SubTask) for task in plan.subtasks)


class TestPlannerIntentDetection:
    """Tests for intent detection and tool selection."""
    
    def test_file_generation_intent(self):
        """Test detection of file generation intent."""
        plan = planner.generate_plan("Generate a PDF report")
        
        # Should have file_writer tool in subtasks
        tools_used = [task.tool for task in plan.subtasks]
        assert "file_writer" in tools_used
    
    def test_note_creation_intent(self):
        """Test detection of note creation intent."""
        plan = planner.generate_plan("Create a note with the meeting summary")
        
        tools_used = [task.tool for task in plan.subtasks]
        assert "notes" in tools_used or "file_writer" in tools_used
    
    def test_email_intent(self):
        """Test detection of email sending intent."""
        plan = planner.generate_plan("Send an email to the team")
        
        tools_used = [task.tool for task in plan.subtasks]
        assert "email" in tools_used
    
    def test_calendar_intent(self):
        """Test detection of calendar event intent."""
        plan = planner.generate_plan("Schedule a meeting for tomorrow at 3pm")
        
        tools_used = [task.tool for task in plan.subtasks]
        assert "calendar" in tools_used
    
    def test_ocr_intent(self):
        """Test detection of OCR processing intent."""
        plan = planner.generate_plan("Extract text from the uploaded image")
        
        tools_used = [task.tool for task in plan.subtasks]
        assert "ocr" in tools_used


class TestPlannerSubtaskStructure:
    """Tests for subtask structure and properties."""
    
    def test_subtask_has_required_fields(self):
        """Test that subtasks have all required fields."""
        plan = planner.generate_plan("Create a document")
        
        for task in plan.subtasks:
            assert hasattr(task, 'step')
            assert hasattr(task, 'action')
            assert hasattr(task, 'tool')
            assert hasattr(task, 'requires_confirmation')
            
            assert isinstance(task.step, int)
            assert isinstance(task.action, str)
            assert isinstance(task.tool, str)
            assert isinstance(task.requires_confirmation, bool)
    
    def test_subtask_step_numbering(self):
        """Test that subtasks are numbered sequentially."""
        plan = planner.generate_plan("Send email and create note")
        
        steps = [task.step for task in plan.subtasks]
        assert steps == list(range(1, len(steps) + 1))
    
    def test_subtask_action_not_empty(self):
        """Test that subtask actions are not empty."""
        plan = planner.generate_plan("Perform multiple tasks")
        
        for task in plan.subtasks:
            assert task.action.strip() != ""
            assert len(task.action) > 5


class TestPlannerWithContext:
    """Tests for planner with additional context."""
    
    def test_plan_with_context_dict(self):
        """Test planning with context dictionary."""
        context = {
            "user_name": "John",
            "project": "ServiBot"
        }
        
        plan = planner.generate_plan("Create a report", context=context)
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.subtasks) > 0
    
    def test_plan_without_context(self):
        """Test planning without context (None)."""
        plan = planner.generate_plan("Simple task", context=None)
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.subtasks) > 0


class TestPlannerEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_message(self):
        """Test planner with empty message."""
        plan = planner.generate_plan("")
        
        # Should still return valid plan (maybe default/error handling)
        assert isinstance(plan, ExecutionPlan)
    
    def test_very_long_message(self):
        """Test planner with very long message."""
        long_message = "Create a document " * 100
        plan = planner.generate_plan(long_message)
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.subtasks) > 0
    
    def test_special_characters_message(self):
        """Test planner with special characters."""
        plan = planner.generate_plan("Create file with émojis 🚀 and ñ characters")
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.subtasks) > 0
    
    def test_multiple_intents(self):
        """Test planner with multiple intents in one message."""
        plan = planner.generate_plan(
            "Send an email, create a PDF report, and schedule a meeting"
        )
        
        # Should create multiple subtasks for multiple intents
        assert len(plan.subtasks) >= 3
        
        tools_used = [task.tool for task in plan.subtasks]
        # Should detect multiple different tools
        assert len(set(tools_used)) >= 2


class TestPlannerConsistency:
    """Tests for planner consistency and repeatability."""
    
    def test_same_input_similar_output(self):
        """Test that same input produces similar plans."""
        message = "Create a PDF document"
        
        plan1 = planner.generate_plan(message)
        plan2 = planner.generate_plan(message)
        
        # Should have similar structure
        assert len(plan1.subtasks) == len(plan2.subtasks)
        
        # Tools should match
        tools1 = [t.tool for t in plan1.subtasks]
        tools2 = [t.tool for t in plan2.subtasks]
        assert tools1 == tools2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
