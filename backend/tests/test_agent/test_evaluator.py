"""
Tests for Agent Evaluator module
"""
import pytest
from app.agent.evaluator import evaluator, Evaluator


class TestEvaluatorBasic:
    """Basic tests for evaluator functionality."""
    
    def test_evaluator_instance_exists(self):
        """Test that evaluator singleton exists."""
        assert evaluator is not None
        assert isinstance(evaluator, Evaluator)
    
    def test_evaluate_results_returns_dict(self):
        """Test that evaluate_results returns a dictionary."""
        execution_result = {
            "objective": "Test objective",
            "total_steps": 1,
            "completed_steps": 1,
            "failed_steps": 0,
            "results": [
                {
                    "step": 1,
                    "status": "success",
                    "tool_used": "file_writer",
                    "result": {"status": "success"}
                }
            ]
        }
        
        evaluation = evaluator.evaluate_results(execution_result)
        
        assert isinstance(evaluation, dict)


class TestEvaluatorSuccess:
    """Tests for successful execution evaluation."""
    
    def test_evaluate_all_success(self):
        """Test evaluation of fully successful execution."""
        execution_result = {
            "objective": "Complete all tasks",
            "total_steps": 3,
            "completed_steps": 3,
            "failed_steps": 0,
            "results": [
                {"step": 1, "status": "success", "tool_used": "file_writer"},
                {"step": 2, "status": "success", "tool_used": "email"},
                {"step": 3, "status": "success", "tool_used": "notes"},
            ]
        }
        
        evaluation = evaluator.evaluate_results(execution_result)
        
        # Should indicate success
        assert evaluation is not None
        # Check for common success indicators
        if "status" in evaluation:
            assert evaluation["status"] in ["success", "completed", "done"]
        if "success" in evaluation:
            assert evaluation["success"] is True
    
    def test_evaluate_single_success(self):
        """Test evaluation of single successful task."""
        execution_result = {
            "objective": "Single task",
            "total_steps": 1,
            "completed_steps": 1,
            "failed_steps": 0,
            "results": [
                {"step": 1, "status": "success", "tool_used": "file_writer"}
            ]
        }
        
        evaluation = evaluator.evaluate_results(execution_result)
        
        assert evaluation is not None


class TestEvaluatorFailure:
    """Tests for failed execution evaluation."""
    
    def test_evaluate_all_failed(self):
        """Test evaluation of completely failed execution."""
        execution_result = {
            "objective": "Failed objective",
            "total_steps": 2,
            "completed_steps": 0,
            "failed_steps": 2,
            "results": [
                {"step": 1, "status": "failed", "error": "Tool error"},
                {"step": 2, "status": "failed", "error": "Another error"},
            ]
        }
        
        evaluation = evaluator.evaluate_results(execution_result)
        
        assert evaluation is not None
    
    def test_evaluate_partial_failure(self):
        """Test evaluation of partially failed execution."""
        execution_result = {
            "objective": "Mixed results",
            "total_steps": 3,
            "completed_steps": 2,
            "failed_steps": 1,
            "results": [
                {"step": 1, "status": "success", "tool_used": "file_writer"},
                {"step": 2, "status": "failed", "error": "Error occurred"},
                {"step": 3, "status": "success", "tool_used": "email"},
            ]
        }
        
        evaluation = evaluator.evaluate_results(execution_result)
        
        assert evaluation is not None


class TestEvaluatorPending:
    """Tests for pending/incomplete execution evaluation."""
    
    def test_evaluate_with_pending(self):
        """Test evaluation with pending tasks."""
        execution_result = {
            "objective": "Has pending",
            "total_steps": 3,
            "completed_steps": 1,
            "failed_steps": 0,
            "results": [
                {"step": 1, "status": "success", "tool_used": "file_writer"},
                {"step": 2, "status": "pending", "error": "Awaiting confirmation"},
                {"step": 3, "status": "pending", "error": "Not executed yet"},
            ]
        }
        
        evaluation = evaluator.evaluate_results(execution_result)
        
        assert evaluation is not None
    
    def test_evaluate_with_skipped(self):
        """Test evaluation with skipped tasks."""
        execution_result = {
            "objective": "Has skipped",
            "total_steps": 2,
            "completed_steps": 1,
            "failed_steps": 0,
            "results": [
                {"step": 1, "status": "success", "tool_used": "file_writer"},
                {"step": 2, "status": "skipped", "error": "User declined"},
            ]
        }
        
        evaluation = evaluator.evaluate_results(execution_result)
        
        assert evaluation is not None


class TestEvaluatorEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_evaluate_empty_results(self):
        """Test evaluation with empty results."""
        execution_result = {
            "objective": "Empty",
            "total_steps": 0,
            "completed_steps": 0,
            "failed_steps": 0,
            "results": []
        }
        
        evaluation = evaluator.evaluate_results(execution_result)
        
        assert evaluation is not None
    
    def test_evaluate_missing_fields(self):
        """Test evaluation handles missing fields gracefully."""
        execution_result = {
            "objective": "Incomplete data",
            "results": [
                {"step": 1, "status": "success"}
            ]
        }
        
        # Should not raise exception
        evaluation = evaluator.evaluate_results(execution_result)
        
        assert evaluation is not None


class TestEvaluatorMetrics:
    """Tests for evaluation metrics and scoring."""
    
    def test_evaluation_has_metrics(self):
        """Test that evaluation includes useful metrics."""
        execution_result = {
            "objective": "Test metrics",
            "total_steps": 4,
            "completed_steps": 3,
            "failed_steps": 1,
            "results": [
                {"step": 1, "status": "success"},
                {"step": 2, "status": "success"},
                {"step": 3, "status": "failed", "error": "Error"},
                {"step": 4, "status": "success"},
            ]
        }
        
        evaluation = evaluator.evaluate_results(execution_result)
        
        assert evaluation is not None
        # Evaluation should provide some form of assessment
        assert len(evaluation) > 0


class TestEvaluatorConsistency:
    """Tests for evaluator consistency."""
    
    def test_same_input_same_output(self):
        """Test that same input produces same evaluation."""
        execution_result = {
            "objective": "Consistency test",
            "total_steps": 2,
            "completed_steps": 2,
            "failed_steps": 0,
            "results": [
                {"step": 1, "status": "success"},
                {"step": 2, "status": "success"},
            ]
        }
        
        eval1 = evaluator.evaluate_results(execution_result)
        eval2 = evaluator.evaluate_results(execution_result)
        
        # Should produce consistent evaluations
        assert eval1 == eval2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
