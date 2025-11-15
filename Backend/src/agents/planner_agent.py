"""
Planner Agent: Divides complex tasks into subtasks using Task Decomposition approach.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY
from agents.graph.resource_manager import get_resource_manager
from agents.graph.context_manager import get_context_manager
from agents.graph.error_handler import get_error_handler


class PlannerAgent:
    """
    Agent that decomposes complex tasks into subtasks.
    Uses Task Decomposition approach with structured planning.
    """
    
    def __init__(self):
        self.resource_manager = get_resource_manager()
        self.context_manager = get_context_manager()
        self.error_handler = get_error_handler()
        self.llm = self.resource_manager.get_llm(model="gpt-4o-mini", temperature=0.3)
    
    def decompose_task(self, task: str, available_tools: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Decompose a complex task into subtasks with dependencies.
        
        Args:
            task: Complex task description
            available_tools: List of available tool names
            
        Returns:
            Dictionary with plan structure:
            {
                "task": original task,
                "subtasks": [
                    {
                        "id": 1,
                        "description": "...",
                        "tool": "ToolName",
                        "dependencies": [],
                        "estimated_time": "..."
                    }
                ],
                "execution_order": [1, 2, 3, ...]
            }
        """
        if not task or not task.strip():
            return {"error": "No task provided for planning"}
        
        try:
            tools_list = ", ".join(available_tools) if available_tools else "all available tools"
            
            prompt = f"""You are an expert planner for a multi-agent astronomical analysis system.

Complex task: {task}

Available tools: {tools_list}

Your task is to decompose this complex task into smaller, manageable subtasks.

For each subtask, identify:
1. Clear description of the subtask
2. Most appropriate tool or agent
3. Dependencies (which subtasks must be completed before)
4. Time/complexity estimate

Respond ONLY with a valid JSON in this format:
{{
    "task": "original task",
    "subtasks": [
        {{
            "id": 1,
            "description": "subtask description",
            "tool": "ToolName",
            "dependencies": [],
            "estimated_complexity": "low|medium|high"
        }}
    ],
    "execution_order": [1, 2, 3]
}}

Make sure the JSON is valid and that execution_order respects dependencies."""

            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to extract JSON from response
            try:
                # Remove markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                plan = json.loads(content)
                
                # Store plan in context
                self.context_manager.set("current_plan", plan)
                self.context_manager.add_tool_result("Planner", plan, {"task": task})
                
                return plan
            except json.JSONDecodeError:
                # Fallback: return structured text plan
                return {
                    "task": task,
                    "plan_text": content,
                    "subtasks": [],
                    "execution_order": []
                }
                
        except Exception as e:
            return {"error": f"Error creating plan: {str(e)}"}
    
    def get_execution_plan(self, task: str, available_tools: Optional[List[str]] = None) -> str:
        """
        Get a human-readable execution plan.
        
        Args:
            task: Task description
            available_tools: Available tools
            
        Returns:
            Formatted execution plan string
        """
        plan = self.decompose_task(task, available_tools)
        
        if "error" in plan:
            return f"Error: {plan['error']}"
        
        if "plan_text" in plan:
            return plan["plan_text"]
        
        # Format structured plan
        output = [f"📋 Execution Plan for: {plan.get('task', task)}\n"]
        output.append("=" * 60 + "\n")
        
        subtasks = plan.get("subtasks", [])
        execution_order = plan.get("execution_order", [])
        
        for step_num in execution_order:
            subtask = next((st for st in subtasks if st.get("id") == step_num), None)
            if subtask:
                output.append(f"\nStep {step_num}: {subtask.get('description', 'N/A')}")
                output.append(f"  Tool: {subtask.get('tool', 'N/A')}")
                deps = subtask.get("dependencies", [])
                if deps:
                    output.append(f"  Dependencies: {', '.join(map(str, deps))}")
                output.append(f"  Complexity: {subtask.get('estimated_complexity', 'N/A')}")
        
        return "\n".join(output)


def planner_agent_tool(task: str, available_tools: Optional[List[str]] = None) -> str:
    """
    Tool function for task decomposition.
    
    Args:
        task: Complex task to decompose
        available_tools: List of available tool names
        
    Returns:
        Execution plan as formatted string
    """
    agent = PlannerAgent()
    return agent.get_execution_plan(task, available_tools)

