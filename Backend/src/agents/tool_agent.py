"""
Tool Agent: Uses external tools (APIs, databases, calculators, visualizations, etc.)
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
import json
import math

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY
from agents.graph.resource_manager import get_resource_manager
from agents.graph.context_manager import get_context_manager
from agents.graph.error_handler import get_error_handler


class ToolAgent:
    """
    Agent that uses external tools and APIs.
    Supports NASA API, calculations, visualizations, etc.
    """
    
    def __init__(self):
        self.resource_manager = get_resource_manager()
        self.context_manager = get_context_manager()
        self.error_handler = get_error_handler()
        self.llm = self.resource_manager.get_llm(model="gpt-4o-mini", temperature=0.3)
    
    def call_nasa_api(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call NASA API endpoints.
        
        Args:
            endpoint: API endpoint (e.g., "apod", "neo/feed")
            params: Query parameters
            
        Returns:
            API response data
        """
        try:
            base_url = "https://api.nasa.gov"
            api_key = "DEMO_KEY"  # Replace with actual NASA API key if available
            
            url = f"{base_url}/{endpoint}"
            params = params or {}
            params["api_key"] = api_key
            
            response = self.error_handler.retry(
                requests.get,
                url,
                params=params,
                timeout=10,
                max_retries=2
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Store in context
            self.context_manager.add_tool_result("NASA_API", data, {"endpoint": endpoint})
            
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def calculate_orbital_parameters(self, mass: float, distance: float, period: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate orbital parameters using Kepler's laws.
        
        Args:
            mass: Mass of central body (kg)
            distance: Orbital distance (m)
            period: Orbital period (s), optional
            
        Returns:
            Calculated orbital parameters
        """
        try:
            G = 6.67430e-11  # Gravitational constant
            
            if period:
                # Calculate semi-major axis from period
                a = ((G * mass * period**2) / (4 * math.pi**2))**(1/3)
            else:
                a = distance
            
            # Orbital velocity
            v = math.sqrt(G * mass / a)
            
            # Escape velocity
            v_escape = math.sqrt(2 * G * mass / a)
            
            result = {
                "semi_major_axis": a,
                "orbital_velocity": v,
                "escape_velocity": v_escape,
                "orbital_period": period or (2 * math.pi * math.sqrt(a**3 / (G * mass)))
            }
            
            self.context_manager.add_tool_result("OrbitalCalculator", result, {
                "mass": mass,
                "distance": distance
            })
            
            return {"status": "success", "parameters": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def calculate_black_hole_parameters(self, mass: float) -> Dict[str, Any]:
        """
        Calculate black hole parameters (Schwarzschild radius, etc.).
        
        Args:
            mass: Black hole mass (kg)
            
        Returns:
            Black hole parameters
        """
        try:
            G = 6.67430e-11  # Gravitational constant
            c = 299792458  # Speed of light (m/s)
            
            # Schwarzschild radius
            r_s = 2 * G * mass / (c**2)
            
            # Event horizon area
            area = 4 * math.pi * r_s**2
            
            # Hawking temperature
            hbar = 1.054571817e-34  # Reduced Planck constant
            k_B = 1.380649e-23  # Boltzmann constant
            T_hawking = (hbar * c**3) / (8 * math.pi * G * mass * k_B)
            
            result = {
                "schwarzschild_radius": r_s,
                "event_horizon_area": area,
                "hawking_temperature": T_hawking,
                "mass": mass
            }
            
            self.context_manager.add_tool_result("BlackHoleCalculator", result, {"mass": mass})
            
            return {"status": "success", "parameters": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def format_tool_result(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Format tool result for display."""
        if result.get("status") == "error":
            return f"Error in {tool_name}: {result.get('error', 'Unknown error')}"
        
        data = result.get("data") or result.get("parameters") or result
        return json.dumps(data, indent=2, ensure_ascii=False)


def tool_agent_tool(tool_type: str, parameters: str) -> str:
    """
    Tool function for using external tools.
    
    Args:
        tool_type: Type of tool ("nasa_api", "orbital_calc", "black_hole_calc")
        parameters: JSON string with parameters
        
    Returns:
        Tool result as formatted string
    """
    agent = ToolAgent()
    
    try:
        params = json.loads(parameters) if isinstance(parameters, str) else parameters
        
        if tool_type == "nasa_api":
            endpoint = params.get("endpoint", "apod")
            api_params = params.get("params", {})
            result = agent.call_nasa_api(endpoint, api_params)
            return agent.format_tool_result("NASA API", result)
        
        elif tool_type == "orbital_calc":
            mass = params.get("mass")
            distance = params.get("distance")
            period = params.get("period")
            if not mass or not distance:
                return "Error: mass and distance are required for orbital calculations"
            result = agent.calculate_orbital_parameters(mass, distance, period)
            return agent.format_tool_result("Orbital Calculator", result)
        
        elif tool_type == "black_hole_calc":
            mass = params.get("mass")
            if not mass:
                return "Error: mass is required for black hole calculations"
            result = agent.calculate_black_hole_parameters(mass)
            return agent.format_tool_result("Black Hole Calculator", result)
        
        else:
            return f"Error: Unknown tool type: {tool_type}. Available: nasa_api, orbital_calc, black_hole_calc"
    
    except json.JSONDecodeError:
        return f"Error: Invalid JSON parameters: {parameters}"
    except Exception as e:
        return f"Error using tool: {str(e)}"

