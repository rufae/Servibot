"""
Agent Evaluator Module
Evaluates execution results and decides on retries or fallbacks.
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class Evaluator:
    """
    Agent evaluator that assesses execution results and suggests improvements.
    """
    
    def __init__(self):
        """Initialize the evaluator."""
        logger.info("Evaluator initialized")
    
    def evaluate_results(
        self,
        execution_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate execution results and provide assessment.
        
        Args:
            execution_results: Results from executor
            
        Returns:
            Evaluation with success metrics and recommendations
        """
        total_steps = execution_results.get("total_steps", 0)
        completed_steps = execution_results.get("completed_steps", 0)
        failed_steps = execution_results.get("failed_steps", 0)
        
        success_rate = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # Determine overall status
        if failed_steps == 0 and completed_steps == total_steps:
            overall_status = "success"
        elif failed_steps > 0 and completed_steps > 0:
            overall_status = "partial_success"
        elif failed_steps > 0 and completed_steps == 0:
            overall_status = "failed"
        else:
            overall_status = "pending"
        
        # Generate recommendations
        recommendations = self._generate_recommendations(execution_results)
        
        evaluation = {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "total_steps": total_steps,
            "recommendations": recommendations,
            "should_retry": failed_steps > 0 and failed_steps < total_steps,
            "retry_steps": self._identify_retry_steps(execution_results)
        }
        
        logger.info(f"Evaluation complete: {overall_status} ({success_rate:.1f}% success rate)")
        return evaluation
    
    def _generate_recommendations(
        self,
        execution_results: Dict[str, Any]
    ) -> List[str]:
        """
        Generate recommendations based on execution results.
        
        Args:
            execution_results: Results from executor
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        results = execution_results.get("results", [])
        for result in results:
            if result["status"] == "failed":
                recommendations.append(
                    f"Step {result['step']} failed: Consider retrying with different parameters"
                )
            elif result["status"] == "pending":
                recommendations.append(
                    f"Step {result['step']} pending: User confirmation required"
                )
        
        if not recommendations:
            recommendations.append("All steps completed successfully")
        
        return recommendations
    
    def _identify_retry_steps(
        self,
        execution_results: Dict[str, Any]
    ) -> List[int]:
        """
        Identify which steps should be retried.
        
        Args:
            execution_results: Results from executor
            
        Returns:
            List of step numbers to retry
        """
        retry_steps = []
        
        results = execution_results.get("results", [])
        for result in results:
            if result["status"] == "failed":
                retry_steps.append(result["step"])
        
        return retry_steps


# Global evaluator instance
evaluator = Evaluator()
