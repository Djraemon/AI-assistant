"""Evaluation and feedback mechanisms for the AI Teaching Assistant."""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class QueryEvaluator:
    """Evaluates the quality of query responses."""
    
    def __init__(self, config):
        self.config = config
        self.evaluation_dir = os.path.join(config.data_config.base_data_dir, "evaluation")
        os.makedirs(self.evaluation_dir, exist_ok=True)
        
    def evaluate_response(self, query: str, response: str, context: List[str] = None) -> Dict[str, Any]:
        """Evaluate the quality of a response based on several criteria."""
        evaluation = {
            "query": query,
            "response_length": len(response),
            "relevance_score": self._calculate_relevance(query, response),
            "completeness_score": self._calculate_completeness(response, context),
            "accuracy_score": self._calculate_accuracy(response),
            "timestamp": datetime.now().isoformat(),
            "overall_score": 0.0
        }
        
        # Calculate overall score as average of individual scores
        evaluation["overall_score"] = (
            evaluation["relevance_score"] + 
            evaluation["completeness_score"] + 
            evaluation["accuracy_score"]
        ) / 3
        
        return evaluation
    
    def _calculate_relevance(self, query: str, response: str) -> float:
        """Calculate relevance score using LlamaIndex's semantic similarity."""
        try:
            # Import the necessary LlamaIndex components
            from llama_index.core.evaluation import SemanticSimilarityEvaluator
            from llama_index.llms.siliconflow import SiliconFlow
            
            # Initialize the evaluator with the same model as the main system
            evaluator = SemanticSimilarityEvaluator(
                llm=SiliconFlow(
                    api_key=self.config.model_config.api_key,
                    model=self.config.model_config.llm_model
                ),
                embed_model=self.config.model_config.embedding_model
            )
            
            # Evaluate the semantic similarity between query and response
            eval_result = evaluator.evaluate(
                query=query,
                response=response
            )
            
            # Return the score, ensuring it's between 0 and 1
            return max(0.0, min(1.0, eval_result.score if eval_result.score is not None else 0.0))
        
        except Exception as e:
            print(f"Error calculating relevance with LlamaIndex evaluator: {e}")
            # Fallback to a basic relevance calculation if the evaluator fails
            return 0.5  # Return neutral score as fallback
    
    def _calculate_completeness(self, response: str, context: List[str] = None) -> float:
        """Calculate completeness score based on response information density."""
        if not response.strip():
            return 0.0
            
        # Score based on length and information density
        words = response.split()
        if len(words) < 10:
            return 0.3  # Too short
        elif len(words) < 30:
            return 0.6  # Moderate
        else:
            return 0.8  # Good length
    
    def _calculate_accuracy(self, response: str) -> float:
        """Calculate accuracy score based on response characteristics."""
        # Simple heuristics for accuracy assessment
        response_lower = response.lower()
        
        # Check for uncertainty phrases that might indicate lower accuracy
        uncertainty_indicators = ["可能", "也许", "大概", "应该是", "我不确定", "无法确定", "根据提供的信息"]
        uncertainty_count = sum(1 for indicator in uncertainty_indicators if indicator in response_lower)
        
        # Lower score if too many uncertainty indicators
        if uncertainty_count > 2:
            return 0.5
        else:
            return 0.8  # Assume generally accurate if not too uncertain


class FeedbackCollector:
    """Collects and manages user feedback on responses."""
    
    def __init__(self, config):
        self.config = config
        self.feedback_dir = os.path.join(config.data_config.base_data_dir, "feedback")
        os.makedirs(self.feedback_dir, exist_ok=True)
        self.feedback_file = os.path.join(self.feedback_dir, "feedback.jsonl")
    
    def collect_feedback(self, query: str, response: str, user_rating: int = None, 
                        user_comment: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Collect user feedback for a query-response pair."""
        feedback_entry = {
            "query": query,
            "response": response,
            "user_rating": user_rating,  # 1-5 scale
            "user_comment": user_comment,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Save feedback to file
        with open(self.feedback_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(feedback_entry, ensure_ascii=False) + '\n')
        
        return feedback_entry
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get a summary of collected feedback."""
        if not os.path.exists(self.feedback_file):
            return {"total_feedback": 0, "average_rating": 0.0, "recent_feedback": []}
        
        feedback_entries = []
        with open(self.feedback_file, 'r', encoding='utf-8') as f:
            for line in f:
                feedback_entries.append(json.loads(line.strip()))
        
        if not feedback_entries:
            return {"total_feedback": 0, "average_rating": 0.0, "recent_feedback": []}
        
        total_rating = sum(f.get("user_rating", 0) for f in feedback_entries if f.get("user_rating"))
        avg_rating = total_rating / len([f for f in feedback_entries if f.get("user_rating")]) if [f for f in feedback_entries if f.get("user_rating")] else 0.0
        
        return {
            "total_feedback": len(feedback_entries),
            "average_rating": round(avg_rating, 2),
            "recent_feedback": feedback_entries[-5:]  # Last 5 feedback entries
        }


class EvaluationManager:
    """Manages evaluation and feedback collection for the entire system."""
    
    def __init__(self, config):
        self.config = config
        self.evaluator = QueryEvaluator(config)
        self.feedback_collector = FeedbackCollector(config)
        self.evaluation_log_file = os.path.join(self.config.data_config.base_data_dir, "evaluation", "evaluations.jsonl")
    
    def evaluate_and_log(self, query: str, response: str, context: List[str] = None, 
                        user_rating: int = None, user_comment: str = None) -> Dict[str, Any]:
        """Evaluate a query-response pair and optionally collect feedback."""
        # Evaluate the response
        evaluation = self.evaluator.evaluate_response(query, response, context)
        
        # Add evaluation metadata to response
        evaluation["query"] = query
        evaluation["response"] = response
        evaluation["context_provided"] = bool(context)
        
        # Log the evaluation
        with open(self.evaluation_log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(evaluation, ensure_ascii=False) + '\n')
        
        # Collect feedback if provided
        if user_rating is not None or user_comment:
            self.feedback_collector.collect_feedback(
                query=query,
                response=response,
                user_rating=user_rating,
                user_comment=user_comment,
                metadata=evaluation
            )
        
        return evaluation
    
    def get_system_performance(self) -> Dict[str, Any]:
        """Get overall system performance metrics."""
        # Get evaluation metrics
        if os.path.exists(self.evaluation_log_file):
            with open(self.evaluation_log_file, 'r', encoding='utf-8') as f:
                evaluations = [json.loads(line.strip()) for line in f]
            
            if evaluations:
                avg_relevance = sum(e["relevance_score"] for e in evaluations) / len(evaluations)
                avg_completeness = sum(e["completeness_score"] for e in evaluations) / len(evaluations)
                avg_accuracy = sum(e["accuracy_score"] for e in evaluations) / len(evaluations)
                avg_overall = sum(e["overall_score"] for e in evaluations) / len(evaluations)
            else:
                avg_relevance = avg_completeness = avg_accuracy = avg_overall = 0.0
        else:
            avg_relevance = avg_completeness = avg_accuracy = avg_overall = 0.0
        
        # Get feedback summary
        feedback_summary = self.feedback_collector.get_feedback_summary()
        
        return {
            "evaluation_metrics": {
                "total_evaluations": len(evaluations) if 'evaluations' in locals() else 0,
                "average_relevance": round(avg_relevance, 2),
                "average_completeness": round(avg_completeness, 2),
                "average_accuracy": round(avg_accuracy, 2),
                "average_overall": round(avg_overall, 2)
            },
            "feedback_summary": feedback_summary
        }


# Example usage function
def example_evaluation_usage():
    """Example of how to use the evaluation system."""
    from config import CONFIG
    
    # Initialize evaluation manager
    eval_manager = EvaluationManager(CONFIG)
    
    # Example query and response
    query = "什么是大数据的4V特征？"
    response = "大数据的4V特征包括：Volume（大量）、Velocity（高速）、Variety（多样）、Veracity（真实性）。"
    context = ["大数据概述", "基本概念"]
    
    # Evaluate and log
    evaluation = eval_manager.evaluate_and_log(
        query=query,
        response=response,
        context=context,
        user_rating=5,  # User rated this response as excellent
        user_comment="解释得很清楚，涵盖了所有要点"
    )
    
    print("Evaluation results:")
    print(f"Relevance Score: {evaluation['relevance_score']}")
    print(f"Completeness Score: {evaluation['completeness_score']}")
    print(f"Accuracy Score: {evaluation['accuracy_score']}")
    print(f"Overall Score: {evaluation['overall_score']}")
    
    # Get system performance
    performance = eval_manager.get_system_performance()
    print("\nSystem Performance:")
    print(f"Total Evaluations: {performance['evaluation_metrics']['total_evaluations']}")
    print(f"Average Overall Score: {performance['evaluation_metrics']['average_overall']}")
    print(f"Average Rating: {performance['feedback_summary']['average_rating']}")


if __name__ == "__main__":
    example_evaluation_usage()