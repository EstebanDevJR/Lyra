"""
API Integration Agent: Queries external services (NASA, ESA, ADS, Wikipedia, etc.)
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import requests
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY
from agents.graph.resource_manager import get_resource_manager
from agents.graph.context_manager import get_context_manager
from agents.graph.error_handler import get_error_handler


class APIIntegrationAgent:
    """
    Agent that integrates with external APIs for astronomical data.
    Supports NASA, ESA, ADS, Wikipedia, etc.
    """
    
    def __init__(self):
        self.resource_manager = get_resource_manager()
        self.context_manager = get_context_manager()
        self.error_handler = get_error_handler()
        self.llm = self.resource_manager.get_llm(model="gpt-4o-mini", temperature=0.3)
    
    def query_nasa_apod(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Query NASA Astronomy Picture of the Day.
        
        Args:
            date: Date in YYYY-MM-DD format (optional, defaults to today)
            
        Returns:
            APOD data
        """
        try:
            url = "https://api.nasa.gov/planetary/apod"
            params = {"api_key": "DEMO_KEY"}
            if date:
                params["date"] = date
            
            response = self.error_handler.retry(
                requests.get,
                url,
                params=params,
                timeout=10,
                max_retries=2
            )
            response.raise_for_status()
            data = response.json()
            
            self.context_manager.add_tool_result("NASA_APOD", data, {"date": date})
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def query_nasa_neo(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Query NASA Near Earth Objects.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            NEO data
        """
        try:
            url = "https://api.nasa.gov/neo/rest/v1/feed"
            params = {
                "api_key": "DEMO_KEY",
                "start_date": start_date,
                "end_date": end_date
            }
            
            response = self.error_handler.retry(
                requests.get,
                url,
                params=params,
                timeout=10,
                max_retries=2
            )
            response.raise_for_status()
            data = response.json()
            
            self.context_manager.add_tool_result("NASA_NEO", data, {
                "start_date": start_date,
                "end_date": end_date
            })
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def query_wikipedia(self, topic: str, lang: str = "es") -> Dict[str, Any]:
        """
        Query Wikipedia for astronomical topics.
        
        Args:
            topic: Topic to search
            lang: Language code (default: "es")
            
        Returns:
            Wikipedia data
        """
        try:
            # Use Wikipedia API
            url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{topic}"
            
            response = self.error_handler.retry(
                requests.get,
                url,
                timeout=10,
                max_retries=2
            )
            response.raise_for_status()
            data = response.json()
            
            self.context_manager.add_tool_result("Wikipedia", data, {"topic": topic, "lang": lang})
            return {"status": "success", "data": data}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def query_ads(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Query NASA ADS (Astrophysics Data System) for papers.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            ADS search results
        """
        try:
            # Note: ADS API requires authentication for full access
            # This is a simplified version
            url = "https://api.adsabs.harvard.edu/v1/search/query"
            headers = {
                "Authorization": "Bearer DEMO_TOKEN"  # Replace with actual token
            }
            params = {
                "q": query,
                "rows": max_results,
                "fl": "title,author,abstract,year"
            }
            
            # For demo purposes, return structured response
            # In production, use actual ADS API
            return {
                "status": "info",
                "message": f"ADS search for '{query}' would return up to {max_results} results. Full ADS API integration requires authentication.",
                "query": query
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def format_api_result(self, service: str, result: Dict[str, Any]) -> str:
        """Format API result for display."""
        if result.get("status") == "error":
            return f"Error querying {service}: {result.get('error', 'Unknown error')}"
        
        data = result.get("data") or result
        
        if service == "NASA_APOD":
            return f"📸 NASA Astronomy Picture of the Day\n\nTitle: {data.get('title', 'N/A')}\n\n{data.get('explanation', 'N/A')[:500]}...\n\nDate: {data.get('date', 'N/A')}"
        
        elif service == "NASA_NEO":
            element_count = data.get("element_count", 0)
            return f"🌍 NASA Near Earth Objects\n\nObjects found: {element_count}\n\nPeriod: {data.get('near_earth_objects', {}).keys() if 'near_earth_objects' in data else 'N/A'}"
        
        elif service == "Wikipedia":
            return f"📚 Wikipedia: {data.get('title', 'N/A')}\n\n{data.get('extract', 'N/A')[:500]}...\n\nURL: {data.get('content_urls', {}).get('desktop', {}).get('page', 'N/A')}"
        
        else:
            return json.dumps(data, indent=2, ensure_ascii=False)


def api_integration_agent_tool(service: str, query: str, **kwargs) -> str:
    """
    Tool function for API integration.
    
    Args:
        service: Service name ("nasa_apod", "nasa_neo", "wikipedia", "ads")
        query: Query or parameters
        **kwargs: Additional parameters
        
    Returns:
        Formatted API result
    """
    agent = APIIntegrationAgent()
    
    try:
        if service.lower() == "nasa_apod":
            date = kwargs.get("date")
            result = agent.query_nasa_apod(date)
            return agent.format_api_result("NASA_APOD", result)
        
        elif service.lower() == "nasa_neo":
            # Parse dates from query or kwargs
            dates = query.split(",") if "," in query else [query]
            start_date = kwargs.get("start_date") or dates[0] if dates else datetime.now().strftime("%Y-%m-%d")
            end_date = kwargs.get("end_date") or dates[1] if len(dates) > 1 else start_date
            result = agent.query_nasa_neo(start_date, end_date)
            return agent.format_api_result("NASA_NEO", result)
        
        elif service.lower() == "wikipedia":
            lang = kwargs.get("lang", "es")
            result = agent.query_wikipedia(query, lang)
            return agent.format_api_result("Wikipedia", result)
        
        elif service.lower() == "ads":
            max_results = kwargs.get("max_results", 5)
            result = agent.query_ads(query, max_results)
            return agent.format_api_result("ADS", result)
        
        else:
            return f"Error: Unknown service: {service}. Available: nasa_apod, nasa_neo, wikipedia, ads"
    
    except Exception as e:
        return f"Error querying API: {str(e)}"

