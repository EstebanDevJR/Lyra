"""
Evaluator Agent: Measures performance of other agents (precision, recall, latency).
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY
from agents.graph.resource_manager import get_resource_manager
from agents.graph.context_manager import get_context_manager
from agents.graph.observer import MetricsObserver


class EvaluatorAgent:
    """
    Agent that evaluates performance of other agents.
    Tracks metrics like precision, recall, latency, accuracy.
    """
    
    def __init__(self):
        self.resource_manager = get_resource_manager()
        self.context_manager = get_context_manager()
        self.llm = self.resource_manager.get_llm(model="gpt-4o-mini", temperature=0.2)
        self.metrics_history: List[Dict[str, Any]] = []
    
    def evaluate_agent_performance(self, agent_name: str, 
                                   input_data: str, 
                                   output_data: str,
                                   expected_output: Optional[str] = None,
                                   execution_time: Optional[float] = None) -> Dict[str, Any]:
        """
        Evaluate agent performance.
        
        Args:
            agent_name: Name of the agent
            input_data: Input provided to agent
            output_data: Output produced by agent
            expected_output: Expected output (optional)
            execution_time: Execution time in seconds (optional)
            
        Returns:
            Evaluation metrics
        """
        try:
            metrics = {
                "agent_name": agent_name,
                "timestamp": datetime.now().isoformat(),
                "input_length": len(input_data),
                "output_length": len(output_data),
                "execution_time": execution_time or 0.0
            }
            
            # Calculate basic metrics
            if execution_time:
                metrics["throughput"] = len(output_data) / execution_time if execution_time > 0 else 0
            
            # Use LLM to evaluate quality if expected output provided
            if expected_output:
                prompt = f"""Evaluate the quality of the agent's output compared to the expected output.

Agent: {agent_name}
Input: {input_data[:500]}...
Obtained output: {output_data[:1000]}...
Expected output: {expected_output[:1000]}...

Evaluate:
1. Precision (0-1): How accurate is the output?
2. Completeness (0-1): How complete is the information?
3. Relevance (0-1): How relevant is it to the input?

Respond ONLY with JSON:
{{
    "precision": 0.0-1.0,
    "completeness": 0.0-1.0,
    "relevance": 0.0-1.0,
    "overall_score": 0.0-1.0
}}"""

                response = self.llm.invoke(prompt)
                content = response.content if hasattr(response, 'content') else str(response)
                
                try:
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    quality_metrics = json.loads(content)
                    metrics.update(quality_metrics)
                except json.JSONDecodeError:
                    pass
            
            # Store metrics
            self.metrics_history.append(metrics)
            self.context_manager.add_tool_result("Evaluator", metrics, {"agent": agent_name})
            
            return metrics
        
        except Exception as e:
            return {"error": str(e), "agent_name": agent_name}
    
    def get_agent_statistics(self, agent_name: str) -> Dict[str, Any]:
        """
        Get statistics for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Statistics dictionary
        """
        agent_metrics = [m for m in self.metrics_history if m.get("agent_name") == agent_name]
        
        if not agent_metrics:
            return {"agent_name": agent_name, "message": "No metrics available"}
        
        total_executions = len(agent_metrics)
        avg_execution_time = sum(m.get("execution_time", 0) for m in agent_metrics) / total_executions
        avg_precision = sum(m.get("precision", 0) for m in agent_metrics if "precision" in m) / max(1, sum(1 for m in agent_metrics if "precision" in m))
        avg_completeness = sum(m.get("completeness", 0) for m in agent_metrics if "completeness" in m) / max(1, sum(1 for m in agent_metrics if "completeness" in m))
        
        return {
            "agent_name": agent_name,
            "total_executions": total_executions,
            "average_execution_time": avg_execution_time,
            "average_precision": avg_precision,
            "average_completeness": avg_completeness,
            "metrics": agent_metrics[-10:]  # Last 10 metrics
        }
    
    def compare_agents(self, agent_names: List[str]) -> str:
        """
        Compare performance of multiple agents.
        
        Args:
            agent_names: List of agent names to compare
            
        Returns:
            Comparison report
        """
        try:
            stats = [self.get_agent_statistics(name) for name in agent_names]
            
            output = ["📊 Agent Comparison\n"]
            output.append("=" * 60 + "\n")
            
            for stat in stats:
                output.append(f"\n{stat['agent_name']}:")
                output.append(f"  Executions: {stat.get('total_executions', 0)}")
                output.append(f"  Average time: {stat.get('average_execution_time', 0):.2f}s")
                if stat.get('average_precision', 0) > 0:
                    output.append(f"  Average precision: {stat.get('average_precision', 0):.2f}")
                if stat.get('average_completeness', 0) > 0:
                    output.append(f"  Average completeness: {stat.get('average_completeness', 0):.2f}")
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error comparing agents: {str(e)}"


def evaluator_agent_tool(agent_name: str, 
                         input_data: str, 
                         output_data: str,
                         expected_output: Optional[str] = None,
                         execution_time: Optional[float] = None) -> str:
    """
    Tool function for evaluating agent performance.
    
    Args:
        agent_name: Name of agent
        input_data: Input data
        output_data: Output data
        expected_output: Expected output (optional)
        execution_time: Execution time (optional)
        
    Returns:
        Evaluation report
    """
    agent = EvaluatorAgent()
    
    try:
        metrics = agent.evaluate_agent_performance(
            agent_name, input_data, output_data, expected_output, execution_time
        )
        
        if "error" in metrics:
            return f"Error: {metrics['error']}"
        
        output = [f"📈 Evaluation of {agent_name}\n"]
        output.append("=" * 60 + "\n")
        output.append(f"Execution time: {metrics.get('execution_time', 0):.2f}s")
        
        if metrics.get("precision"):
            output.append(f"Precision: {metrics['precision']:.2f}")
        if metrics.get("completeness"):
            output.append(f"Completeness: {metrics['completeness']:.2f}")
        if metrics.get("relevance"):
            output.append(f"Relevance: {metrics['relevance']:.2f}")
        if metrics.get("overall_score"):
            output.append(f"Overall score: {metrics['overall_score']:.2f}")
        
        return "\n".join(output)
    
    except Exception as e:
        return f"Error in evaluation: {str(e)}"

