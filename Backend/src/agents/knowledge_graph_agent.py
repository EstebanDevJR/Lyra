"""
Knowledge Graph Agent: Builds and queries relationships between concepts.
Combines RAG + graph knowledge.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import re
import json

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY
from agents.graph.resource_manager import get_resource_manager
from agents.graph.context_manager import get_context_manager
from agents.graph.error_handler import get_error_handler
from core.vectorstore import VectorStore


class KnowledgeGraphAgent:
    """
    Agent that builds and queries knowledge graphs.
    Extracts entities and relationships from text and stores them.
    """
    
    def __init__(self):
        self.resource_manager = get_resource_manager()
        self.context_manager = get_context_manager()
        self.error_handler = get_error_handler()
        self.llm = self.resource_manager.get_llm(model="gpt-4o-mini", temperature=0.2)
        self.graph: Dict[str, Dict[str, any]] = {}
        self._load_graph()
    
    def _load_graph(self):
        """Load knowledge graph from context if available."""
        stored_graph = self.context_manager.get("knowledge_graph")
        if stored_graph:
            self.graph = stored_graph
    
    def _save_graph(self):
        """Save knowledge graph to context."""
        self.context_manager.set("knowledge_graph", self.graph)
    
    def extract_entities_and_relationships(self, text: str) -> Dict[str, any]:
        """
        Extract entities and relationships from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with entities and relationships
        """
        try:
            prompt = f"""Extract scientific entities and their relationships from the following text about astronomy/astrophysics.

Text:
{text[:3000]}

Respond ONLY with a valid JSON in this format:
{{
    "entities": [
        {{
            "name": "entity name",
            "type": "object|concept|measurement|process",
            "properties": {{"property": "value"}}
        }}
    ],
    "relationships": [
        {{
            "source": "source_entity",
            "target": "target_entity",
            "type": "relationship_type",
            "description": "description"
        }}
    ]
}}

Common relationship types: contains, causes, related_to, measures, calculates, describes"""

            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                extracted = json.loads(content)
                return extracted
            except json.JSONDecodeError:
                # Fallback: return basic structure
                return {"entities": [], "relationships": []}
        
        except Exception as e:
            return {"entities": [], "relationships": [], "error": str(e)}
    
    def build_graph(self, text: str) -> str:
        """
        Build knowledge graph from text.
        
        Args:
            text: Text to process
            
        Returns:
            Summary of graph building
        """
        try:
            extracted = self.extract_entities_and_relationships(text)
            
            if "error" in extracted:
                return f"Error extracting entities: {extracted['error']}"
            
            entities = extracted.get("entities", [])
            relationships = extracted.get("relationships", [])
            
            # Add entities to graph
            for entity in entities:
                entity_name = entity.get("name", "").lower()
                if entity_name:
                    if entity_name not in self.graph:
                        self.graph[entity_name] = {
                            "type": entity.get("type", "concept"),
                            "properties": entity.get("properties", {}),
                            "relationships": []
                        }
                    else:
                        # Merge properties
                        self.graph[entity_name]["properties"].update(entity.get("properties", {}))
            
            # Add relationships
            for rel in relationships:
                source = rel.get("source", "").lower()
                target = rel.get("target", "").lower()
                
                if source and target and source in self.graph:
                    self.graph[source]["relationships"].append({
                        "target": target,
                        "type": rel.get("type", "related_to"),
                        "description": rel.get("description", "")
                    })
            
            self._save_graph()
            
            return f"Knowledge graph updated:\n- Entities: {len(entities)}\n- Relationships: {len(relationships)}\n- Total in graph: {len(self.graph)} entities"
        
        except Exception as e:
            return f"Error building graph: {str(e)}"
    
    def query_graph(self, entity: str, depth: int = 2) -> str:
        """
        Query knowledge graph for relationships.
        
        Args:
            entity: Entity to query
            depth: Depth of relationship traversal
            
        Returns:
            Graph query results
        """
        try:
            entity_lower = entity.lower()
            
            if entity_lower not in self.graph:
                # Try semantic search in vector store
                vector_store = self.resource_manager.get_vector_store()
                results = vector_store.search(entity, k=3)
                
                if results:
                    return f"Entity '{entity}' not found directly in graph, but found related information in documents:\n\n" + "\n".join([
                        f"- {r.get('text', '')[:200]}..." for r in results
                    ])
                else:
                    return f"Entity '{entity}' not found in knowledge graph or documents."
            
            node = self.graph[entity_lower]
            output = [f"📊 Entity: {entity}"]
            output.append(f"Type: {node.get('type', 'N/A')}")
            
            if node.get("properties"):
                output.append("\nProperties:")
                for key, value in node["properties"].items():
                    output.append(f"  - {key}: {value}")
            
            if node.get("relationships"):
                output.append("\nRelationships:")
                for rel in node["relationships"][:10]:  # Limit to 10
                    target = rel.get("target", "")
                    rel_type = rel.get("type", "")
                    desc = rel.get("description", "")
                    output.append(f"  - {rel_type}: {target}")
                    if desc:
                        output.append(f"    ({desc})")
            
            return "\n".join(output)
        
        except Exception as e:
            return f"Error querying graph: {str(e)}"
    
    def find_path(self, source: str, target: str) -> str:
        """
        Find path between two entities in the graph.
        
        Args:
            source: Source entity
            target: Target entity
            
        Returns:
            Path description
        """
        try:
            source_lower = source.lower()
            target_lower = target.lower()
            
            if source_lower not in self.graph:
                return f"Entity '{source}' not found in graph."
            if target_lower not in self.graph:
                return f"Entity '{target}' not found in graph."
            
            # Simple BFS to find path
            visited = set()
            queue = [(source_lower, [source_lower])]
            
            while queue:
                current, path = queue.pop(0)
                
                if current == target_lower:
                    return f"Path found: {' → '.join(path)}"
                
                if current in visited or current not in self.graph:
                    continue
                
                visited.add(current)
                
                for rel in self.graph[current].get("relationships", []):
                    next_entity = rel.get("target", "").lower()
                    if next_entity and next_entity not in visited:
                        queue.append((next_entity, path + [next_entity]))
            
            return f"No path found between '{source}' and '{target}' in graph."
        
        except Exception as e:
            return f"Error finding path: {str(e)}"


def knowledge_graph_agent_tool(text: str, operation: str = "build", **kwargs) -> str:
    """
    Tool function for knowledge graph operations.
    
    Args:
        text: Text to process or entity to query
        operation: Operation type ("build", "query", "find_path")
        **kwargs: Additional parameters (entity, target, etc.)
        
    Returns:
        Graph operation result
    """
    agent = KnowledgeGraphAgent()
    
    try:
        if operation == "build":
            return agent.build_graph(text)
        
        elif operation == "query":
            entity = kwargs.get("entity") or text
            depth = kwargs.get("depth", 2)
            return agent.query_graph(entity, depth)
        
        elif operation == "find_path":
            source = kwargs.get("source") or text.split(",")[0].strip()
            target = kwargs.get("target") or text.split(",")[1].strip() if "," in text else ""
            if not target:
                return "Error: source and target required for find_path"
            return agent.find_path(source, target)
        
        else:
            return f"Error: Unknown operation: {operation}. Available: build, query, find_path"
    
    except Exception as e:
        return f"Error in graph operation: {str(e)}"

