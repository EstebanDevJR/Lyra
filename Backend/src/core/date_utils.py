"""
Date and time utilities for providing temporal context to agents.
"""

from datetime import datetime
from typing import Dict


def get_current_date_info() -> Dict[str, str]:
    """
    Get current date and time information formatted for agent context.
    
    Returns:
        Dictionary with formatted date/time information
    """
    now = datetime.now()
    
    return {
        "current_date": now.strftime("%Y-%m-%d"),
        "current_date_formatted": now.strftime("%d de %B de %Y"),
        "current_date_spanish": now.strftime("%d de %B de %Y"),
        "current_time": now.strftime("%H:%M:%S"),
        "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "day_of_week": now.strftime("%A"),
        "day_of_week_spanish": _get_spanish_day(now.strftime("%A")),
        "month": now.strftime("%B"),
        "month_spanish": _get_spanish_month(now.strftime("%B")),
        "year": str(now.year),
        "day": str(now.day),
        "month_number": str(now.month)
    }


def _get_spanish_day(day: str) -> str:
    """Convert English day name to Spanish."""
    days = {
        "Monday": "lunes",
        "Tuesday": "martes",
        "Wednesday": "miércoles",
        "Thursday": "jueves",
        "Friday": "viernes",
        "Saturday": "sábado",
        "Sunday": "domingo"
    }
    return days.get(day, day)


def _get_spanish_month(month: str) -> str:
    """Convert English month name to Spanish."""
    months = {
        "January": "enero",
        "February": "febrero",
        "March": "marzo",
        "April": "abril",
        "May": "mayo",
        "June": "junio",
        "July": "julio",
        "August": "agosto",
        "September": "septiembre",
        "October": "octubre",
        "November": "noviembre",
        "December": "diciembre"
    }
    return months.get(month, month)


def get_date_context_string() -> str:
    """
    Get a formatted string with current date information for agent prompts.
    
    Returns:
        Formatted string with date context
    """
    date_info = get_current_date_info()
    return f"""FECHA ACTUAL: {date_info['current_date_spanish']} ({date_info['current_date']})
DÍA DE LA SEMANA: {date_info['day_of_week_spanish'].capitalize()}
AÑO ACTUAL: {date_info['year']}
MES ACTUAL: {date_info['month_spanish'].capitalize()}

IMPORTANTE: 
- Cuando el usuario mencione "hoy", "actualmente", "recientes", "hasta ahora", "hasta hoy", o fechas específicas, 
  usa esta información como referencia temporal. 
- NO menciones tu fecha de corte de entrenamiento (como "octubre de 2023"). En su lugar, usa la fecha actual proporcionada arriba.
- Si el usuario pregunta "hasta hoy" o "hasta ahora", responde usando la fecha actual mostrada arriba.
- Si mencionan fechas futuras respecto a la fecha actual, indica que no puedes proporcionar información sobre eventos futuros.
- Cuando hables de información hasta una fecha, usa la fecha actual proporcionada, no tu fecha de corte de conocimiento."""

