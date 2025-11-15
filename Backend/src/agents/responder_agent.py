"""
Responder Agent: Generates the final response for the user, combining results from other tools.
Includes personality, emotion detection, and natural dialogue enhancement.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY
from agents.graph.resource_manager import get_resource_manager
from agents.graph.context_manager import get_context_manager


# Personality configurations
PERSONALITIES = {
    "scientific": {
        "tone": "formal y preciso",
        "style": "Usa terminología científica precisa y cita fuentes cuando sea posible.",
    },
    "friendly": {
        "tone": "amigable y accesible",
        "style": "Explica conceptos complejos de manera sencilla y usa analogías.",
    },
    "enthusiastic": {
        "tone": "entusiasta y apasionado",
        "style": "Muestra entusiasmo por los descubrimientos astronómicos y usa lenguaje vívido.",
    },
    "professional": {
        "tone": "profesional y conciso",
        "style": "Proporciona información clara y estructurada, enfocándote en hechos.",
    },
    "casual": {
        "tone": "casual y accesible",
        "style": "Usa lenguaje accesible manteniendo precisión científica. Explica conceptos complejos de manera simple.",
    },
    "detailed": {
        "tone": "detallado y comprehensivo",
        "style": "Proporciona información comprehensiva con explicaciones y contexto.",
    },
    "brief": {
        "tone": "conciso y directo",
        "style": "Proporciona una respuesta concisa enfocándote en los puntos más importantes.",
    }
}


def detect_user_emotion(user_message: str) -> str:
    """
    Detect user emotion from message.
    
    Args:
        user_message: User's message
        
    Returns:
        Detected emotion ("curious", "confused", "excited", "neutral", etc.)
    """
    if not user_message:
        return "neutral"
    
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=OPENAI_API_KEY
        )
        
        prompt = f"""Analyze the following user message and determine their emotional state or attitude.

Message: {user_message[:200]}

Respond ONLY with one of these emotions: curious, confused, excited, neutral, frustrated, amazed

Emotion:"""

        response = llm.invoke(prompt)
        emotion = response.content.strip().lower() if hasattr(response, 'content') else "neutral"
        
        # Store in context
        context_manager = get_context_manager()
        context_manager.set("user_emotion", emotion)
        
        return emotion
    except Exception:
        return "neutral"


def responder_tool(context: str, user_query: Optional[str] = None, 
                   style: str = "scientific", personality: Optional[str] = None,
                   detect_emotion: bool = True) -> str:
    """
    Tool function for generating the final response for the user.
    Includes personality, emotion detection, and natural dialogue enhancement.
    
    Args:
        context: Combined context from other tools (summaries, analysis, etc.)
        user_query: Original user query (if available)
        style: Response style ("scientific", "casual", "detailed", "brief", "friendly", "enthusiastic", "professional")
        personality: Optional personality override (if None, uses style)
        detect_emotion: If True, detects user emotion from query
        
    Returns:
        Final formatted response with personality and natural dialogue
    """
    if not context:
        return "No context provided to generate a response."
    
    try:
        # Initialize LLM
        resource_manager = get_resource_manager()
        context_manager = get_context_manager()
        llm = resource_manager.get_llm(model="gpt-4o-mini", temperature=0.7)
        
        # Determine personality
        selected_personality = personality or style
        personality_config = PERSONALITIES.get(selected_personality, PERSONALITIES["scientific"])
        
        # Detect emotion if enabled
        user_emotion = "neutral"
        emotion_context = ""
        if detect_emotion and user_query:
            user_emotion = detect_user_emotion(user_query)
            if user_emotion != "neutral":
                emotion_context = f" The user seems to be {user_emotion}."
        
        # Build prompt
        query_part = f"\n\nUser question: {user_query}" if user_query else ""
        
        # Get current date context
        from core.date_utils import get_date_context_string
        date_context = get_date_context_string()
        
        prompt = f"""You are Lyra, an AI assistant specialized in astronomical, astrophysical, and nature-related scientific analysis with a {personality_config['tone']} personality.

{date_context}

SCOPE GUIDELINES:
- Your PRIMARY focus is: astrophysics, astronomy, space phenomena, galaxies, stars, planets, black holes, solar storms, auroras, cosmic radiation, nature, Earth sciences, geology, climate, ecology, and related scientific topics.
- You should REFUSE questions about: politics, current events (non-scientific), history (non-scientific), personal opinions, biographies of non-scientists, or clearly off-topic subjects.
- IMPORTANT: Be PERMISSIVE with scientific queries. If a question mentions scientific terms (NGC, mass, pattern, attenuation, objects, etc.), astronomical objects, or seems to be a scientific question, you should answer it.
- Only redirect users if the question is CLEARLY outside your scope (e.g., "who was JFK?" or "what do you think about politics?").
- For ambiguous queries, err on the side of answering them as they might be scientific questions.

{personality_config['style']}

Your task is to generate a clear and precise response in Spanish based on the following context.{query_part}
{emotion_context}

Analysis context:
{context[:3000]}

Instructions:
- Respond in Spanish
- Maintain scientific accuracy
- Add natural transitions between ideas
- Show empathy when appropriate (especially if user is confused)
- Show enthusiasm for astronomical discoveries when relevant
- If context mentions specific values (masses, distances, etc.), include them
- Structure your response clearly
- End with a brief conclusion or summary if appropriate
- When in doubt about whether a query is scientific, answer it rather than refusing
- IMPORTANT: Use the current date provided above as your reference. When the user asks about "hasta hoy", "hasta ahora", "recientes", or similar temporal references, use the current date shown above. Do NOT mention your training data cutoff date (like "octubre de 2023"). Instead, use the current date provided and say "hasta [fecha actual]" or similar.

Generate your response:"""

        response = llm.invoke(prompt)
        
        result = response.content if hasattr(response, 'content') else str(response)
        
        # Store in context
        context_manager.add_tool_result("Responder", result, {
            "style": style,
            "personality": selected_personality,
            "user_emotion": user_emotion,
            "context_length": len(context)
        })
        
        return result
            
    except Exception as e:
        # Fallback response
        return f"Based on the analysis:\n\n{context[:500]}...\n\n(Note: Error generating enhanced response: {str(e)})"


def format_response(results: Dict[str, str], user_query: Optional[str] = None) -> str:
    """
    Format multiple tool results into a coherent response.
    
    Args:
        results: Dictionary with tool names as keys and their outputs as values
        user_query: Original user query
        
    Returns:
        Formatted response
    """
    # Combine results
    context_parts = []
    
    for tool_name, output in results.items():
        if output and output.strip():
            context_parts.append(f"[{tool_name}]\n{output}\n")
    
    context = "\n".join(context_parts)
    
    return responder_tool(context, user_query=user_query, style="scientific")

