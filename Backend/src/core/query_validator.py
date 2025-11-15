"""
Query Validator: Validates user queries to ensure they are within the system's scope.

This module provides security against prompt injection and ensures queries are
related to astrophysics, space, nature, and related scientific topics.
"""

import re
import logging
from typing import Tuple, List, Optional
from langchain_openai import ChatOpenAI
from config import OPENAI_API_KEY

logger = logging.getLogger("lyra.validator")

# Allowed topics keywords (Spanish and English)
ALLOWED_TOPICS = {
    # Space and astronomy
    'espacio', 'espacial', 'astronomía', 'astronómico', 'astrofísica', 'astrofísico',
    'galaxia', 'galaxias', 'estrella', 'estrellas', 'planeta', 'planetas',
    'sistema solar', 'sol', 'luna', 'tierra', 'marte', 'júpiter', 'saturno',
    'nebulosa', 'nebulosas', 'agujero negro', 'agujeros negros', 'quasar',
    'supernova', 'supernovas', 'cometa', 'cometas', 'asteroide', 'asteroides',
    'meteorito', 'meteoritos', 'órbita', 'órbitas', 'constelación', 'constelaciones',
    'telescopio', 'telescopios', 'observatorio', 'observatorios',
    'tormenta solar', 'tormentas solares', 'eyección de masa coronal', 'cme',
    'aurora', 'auroras', 'magnetosfera', 'radiación cósmica',
    # Technical astrophysics terms
    'ngc', 'masa', 'masas', 'objeto', 'objetos', 'patrón', 'patrones',
    'atenuación', 'intervalo', 'estimada', 'estimado', 'distancia', 'distancias',
    'luminosidad', 'temperatura', 'velocidad', 'frecuencia', 'período', 'períodos',
    'espectro', 'espectros', 'longitud de onda', 'redshift', 'corrimiento al rojo',
    'magnitud', 'magnitudes', 'brillo', 'brillantez', 'flujo', 'flujos',
    # Space agencies and organizations
    'nasa', 'esa', 'cern', 'lhc', 'telescopio', 'telescopios', 'sonda', 'sondas',
    'satélite', 'satélites', 'misión', 'misiones', 'rover', 'mars', 'marte',
    # Document and analysis terms
    'documento', 'documentos', 'archivo', 'archivos', 'texto', 'textos',
    'resume', 'resumen', 'resumir', 'analiza', 'analizar', 'análisis',
    'explica', 'explicar', 'describe', 'describir', 'información', 'datos',
    'adjunt', 'subi', 'subí', 'carg', 'adjunté', 'adjuntaste',
    'enumera', 'enumere', 'listar', 'lista', 'según', 'informe', 'reporte',
    'anomalía', 'anomalías', 'señal', 'señales', 'detección', 'detectadas',
    'hipótesis', 'probabilidad', 'probabilidades', 'sección', 'secciones',
    
    # Nature and Earth sciences
    'naturaleza', 'natural', 'ciencia', 'científico', 'científica',
    'física', 'química', 'biología', 'geología', 'meteorología',
    'clima', 'climático', 'medio ambiente', 'ecología', 'ecológico',
    'biodiversidad', 'especies', 'animales', 'plantas', 'ecosistema',
    'océano', 'océanos', 'mar', 'mares', 'atmósfera', 'atmósferico',
    'geología', 'geológico', 'terremoto', 'terremotos', 'volcán', 'volcanes',
    
    # General scientific concepts
    'investigación', 'investigar', 'estudio', 'estudiar', 'análisis',
    'experimento', 'experimentos', 'teoría', 'teorías', 'hipótesis',
    'descubrimiento', 'descubrimientos', 'observación', 'observaciones',
    
    # English equivalents
    'space', 'astronomy', 'astronomical', 'astrophysics', 'astrophysical',
    'galaxy', 'galaxies', 'star', 'stars', 'planet', 'planets',
    'solar system', 'sun', 'moon', 'earth', 'mars', 'jupiter', 'saturn',
    'nebula', 'black hole', 'black holes', 'quasar', 'supernova', 'comet',
    'asteroid', 'meteorite', 'orbit', 'constellation', 'telescope',
    'observatory', 'solar storm', 'coronal mass ejection', 'aurora',
    'magnetosphere', 'cosmic radiation',
    'nature', 'natural', 'science', 'scientific', 'physics', 'chemistry',
    'biology', 'geology', 'meteorology', 'climate', 'environment', 'ecology',
    'biodiversity', 'species', 'animals', 'plants', 'ecosystem', 'ocean',
    'atmosphere', 'earthquake', 'volcano', 'research', 'study', 'analysis',
    'experiment', 'theory', 'hypothesis', 'discovery', 'observation'
}

# Blocked topics keywords (topics outside scope)
BLOCKED_TOPICS = {
    # Politics and current events
    'política', 'político', 'políticos', 'elección', 'elecciones',
    'presidente', 'gobierno', 'partido', 'votar', 'voto',
    'conflicto', 'guerra', 'guerras', 'país', 'países',
    'political', 'politics', 'election', 'president',
    'government', 'party', 'vote', 'conflict', 'war', 'country', 'countries',
    
    # Personal opinions and preferences
    'opinas', 'opinión', 'apoyas', 'apoyo', 'prefieres', 'preferencia',
    'opinion', 'support', 'prefer', 'preference',
    
    # Off-topic general knowledge (people, biographies outside science)
    'quien fue', 'quien es', 'quienes son', 'biografía', 'biografías',
    'who was', 'who is', 'biography', 'biographies',
    
    # Explicit prompt injection attempts
    'ignora', 'olvida', 'no eres', 'eres un', 'actúa como',
    'ignore', 'forget', 'you are not', 'you are a', 'act as',
    'sistema', 'instrucciones', 'prompt', 'system', 'instructions'
}

# Prompt injection patterns
INJECTION_PATTERNS = [
    r'ignore\s+(all\s+)?(previous\s+)?(instructions|prompts|rules)',
    r'forget\s+(all\s+)?(previous\s+)?(instructions|prompts|rules)',
    r'you\s+are\s+(not\s+)?(a\s+)?(assistant|ai|bot|system)',
    r'act\s+as\s+(if\s+)?(you\s+are\s+)?(a\s+)?',
    r'new\s+(instructions|prompt|system|rules)',
    r'override\s+(previous\s+)?(instructions|prompts|rules)',
    r'olvida\s+(todas\s+)?(las\s+)?(instrucciones|reglas)',
    r'ignora\s+(todas\s+)?(las\s+)?(instrucciones|reglas)',
    r'no\s+eres\s+(un\s+)?(asistente|sistema|bot)',
    r'actúa\s+como\s+(si\s+)?(fueras\s+)?(un\s+)?',
    r'nuevas\s+(instrucciones|reglas|sistema)',
    r'anula\s+(las\s+)?(instrucciones|reglas)',
]


def validate_query_topic(query: str, use_llm: bool = True, has_file: bool = False) -> Tuple[bool, Optional[str]]:
    """
    Validate if a query is within the allowed topics (astrophysics, space, nature).
    
    Args:
        query: User query string
        use_llm: If True, use LLM for semantic validation (more accurate but slower)
        has_file: If True, user has uploaded a file, so be more permissive with document-related queries
        
    Returns:
        Tuple of (is_valid, rejection_reason)
        - is_valid: True if query is within scope
        - rejection_reason: None if valid, otherwise reason for rejection
    """
    query_lower = query.lower().strip()
    
    # Check for prompt injection patterns
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, query_lower, re.IGNORECASE):
            logger.warning(f"Prompt injection detected: {query[:100]}")
            return False, "Esta consulta contiene patrones que intentan modificar el comportamiento del sistema."
    
    # If user has uploaded a file, be more permissive with document-related queries
    if has_file:
        # Allow queries about documents, analysis, summaries, etc.
        document_keywords = ['documento', 'archivo', 'texto', 'resume', 'resumen', 'analiza', 
                           'explica', 'describe', 'información', 'datos', 'adjunt', 'subi', 
                           'carg', 'acerca de', 'sobre el', 'del documento', 'del archivo']
        if any(keyword in query_lower for keyword in document_keywords):
            return True, None
    
    # Check for explicitly blocked topics (only reject if clearly political/personal)
    # Be more lenient - only block if query contains multiple blocked keywords
    blocked_count = sum(1 for blocked in BLOCKED_TOPICS if blocked in query_lower)
    
    # Only reject if query has multiple blocked terms AND no scientific terms
    has_allowed_topic = any(topic in query_lower for topic in ALLOWED_TOPICS)
    
    # If query has scientific terms, allow it even if it has some blocked terms
    if has_allowed_topic:
        return True, None
    
    # Special handling for very short queries (likely follow-ups or continuations)
    # If they mention scientific terms, allow them
    query_words = query.split()
    if len(query_words) <= 4:
        # Check for scientific keywords even in short queries
        scientific_keywords = ['nasa', 'cern', 'esa', 'lhc', 'telescopio', 'sonda', 
                             'satélite', 'misión', 'rover', 'mars', 'marte', 'espacio',
                             'astronomía', 'astrofísica', 'estrella', 'planeta', 'galaxia',
                             'descubrimiento', 'descubrimientos', 'investigación']
        if any(keyword in query_lower for keyword in scientific_keywords):
            return True, None
        # Allow very short queries (likely follow-ups or greetings)
        if len(query_words) <= 3:
            return True, None
    
    # If query has multiple blocked terms and no scientific terms, reject
    if blocked_count >= 2:
        logger.warning(f"Blocked topic detected: {blocked_count} blocked terms")
        return False, "Lo siento, solo puedo responder preguntas relacionadas con astrofísica, espacio y naturaleza. Tu consulta parece estar fuera de estos temas."
    
    # Check for allowed topics
    # If no allowed topic found and query is substantial, use LLM for semantic check
    if not has_allowed_topic and use_llm and len(query_words) > 3:
        return _validate_with_llm(query)
    
    # Default: allow query if we got here (be permissive)
    return True, None


def _validate_with_llm(query: str) -> Tuple[bool, Optional[str]]:
    """
    Use LLM to semantically validate if query is about allowed topics.
    
    Args:
        query: User query string
        
    Returns:
        Tuple of (is_valid, rejection_reason)
    """
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            openai_api_key=OPENAI_API_KEY
        )
        
        validation_prompt = f"""Eres un validador de consultas para un asistente de astrofísica.

Tu tarea es determinar si una consulta del usuario está relacionada con los temas permitidos:
- Astrofísica y astronomía (galaxias, estrellas, planetas, agujeros negros, NGC, objetos astronómicos, etc.)
- Espacio y fenómenos espaciales (tormentas solares, auroras, etc.)
- Naturaleza y ciencias de la Tierra (geología, clima, ecología, etc.)
- Física, química, biología y otras ciencias naturales
- Conceptos científicos generales relacionados con estos temas (masa, distancia, patrón, atenuación, intervalo, etc.)
- Preguntas técnicas sobre objetos astronómicos, mediciones científicas, análisis de datos

IMPORTANTE: Sé PERMISIVO. Si la consulta menciona términos científicos, objetos astronómicos (como NGC), conceptos físicos, o parece ser una pregunta científica, responde "SI".

Solo RECHAZA si la consulta es claramente sobre:
- Política, gobierno, elecciones, conflictos políticos (sin contexto científico)
- Historia no científica (biografías de políticos, eventos históricos no científicos)
- Personas fuera del ámbito científico (políticos, figuras históricas no científicas)
- Opiniones personales o preferencias políticas

Responde SOLO con "SI" si la consulta está relacionada con los temas permitidos, o "NO" si está claramente fuera de estos temas.

Consulta del usuario: "{query}"

Respuesta:"""
        
        response = llm.invoke(validation_prompt).content.strip().upper()
        
        if response.startswith("SI") or response.startswith("YES"):
            return True, None
        else:
            return False, "Lo siento, solo puedo responder preguntas relacionadas con astrofísica, espacio y naturaleza. Por favor, reformula tu consulta sobre estos temas."
            
    except Exception as e:
        logger.error(f"Error in LLM validation: {str(e)}")
        # Fallback: if LLM fails, be permissive but log warning
        return True, None


def sanitize_query(query: str) -> str:
    """
    Sanitize query to prevent prompt injection.
    
    Args:
        query: Raw user query
        
    Returns:
        Sanitized query
    """
    # Remove common injection attempts
    sanitized = query
    
    # Remove system instruction attempts
    for pattern in INJECTION_PATTERNS:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
    
    # Remove excessive whitespace
    sanitized = ' '.join(sanitized.split())
    
    return sanitized.strip()

