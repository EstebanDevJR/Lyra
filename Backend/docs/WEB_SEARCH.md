# 🔍 Búsqueda Web con DuckDuckGo

El sistema ahora incluye capacidades de búsqueda web en tiempo real usando DuckDuckGo.

## 🛠️ Herramientas Disponibles

### 1. **Researcher Tool** (Recomendado)
Herramienta inteligente que:
- Realiza búsqueda web usando DuckDuckGo
- Sintetiza los resultados con contexto científico
- Proporciona información contextualizada en español

**Uso:**
```python
from agents.additional_tools import researcher_tool

# Búsqueda web con síntesis científica
result = researcher_tool("últimos descubrimientos sobre agujeros negros", source="web")
```

### 2. **WebSearch Tool**
Búsqueda web directa que retorna resultados crudos:
- Títulos de resultados
- Descripciones
- URLs

**Uso:**
```python
from agents.additional_tools import web_search_tool

# Búsqueda directa
results = web_search_tool("Event Horizon Telescope M87", max_results=5)
```

## 📦 Instalación

Las dependencias ya están incluidas en `requirements.txt`:
- `duckduckgo-search`: Para búsquedas web
- `beautifulsoup4`: Para parsing HTML (opcional, para futuras mejoras)
- `requests`: Para requests HTTP (opcional)

Instalar con:
```bash
pip install -r requirements.txt
```

## 🚀 Uso en el Sistema

Las herramientas están automáticamente disponibles para el agente supervisor:

### Ejemplo de Consulta:
```
Usuario: "¿Cuáles son los últimos descubrimientos sobre agujeros negros?"

El agente puede usar:
- Researcher: Para obtener información sintetizada con contexto científico
- WebSearch: Para obtener resultados directos de búsqueda
```

## 🔧 Configuración

No se requiere configuración adicional. DuckDuckGo no requiere API keys.

## 📝 Ejemplo de Respuesta

**Researcher Tool:**
```
Resultados de búsqueda web para 'agujeros negros':

[Información sintetizada con contexto científico]

---
Fuentes consultadas:
Resultado 1:
Título: [Título del resultado]
Descripción: [Descripción]
URL: [URL]
...
```

**WebSearch Tool:**
```
Resultado 1:
Título: [Título]
Descripción: [Descripción]
URL: [URL]

---
Resultado 2:
...
```

## ⚙️ Características

- ✅ Búsqueda en tiempo real
- ✅ Sin necesidad de API keys
- ✅ Resultados formateados
- ✅ Integración con síntesis científica (Researcher)
- ✅ **Aprendizaje continuo**: Los resultados se agregan automáticamente al vector store (Pinecone)
- ✅ Manejo de errores robusto
- ✅ Fallback a LLM si DuckDuckGo no está disponible

## 🎯 Cuándo Usar Cada Herramienta

- **Researcher**: Cuando necesitas información contextualizada y sintetizada con enfoque científico
- **WebSearch**: Cuando necesitas resultados directos y rápidos de búsqueda web

## 🔍 Ventajas de DuckDuckGo

- ✅ No requiere API keys
- ✅ Respeta la privacidad
- ✅ Gratuito y sin límites
- ✅ Resultados relevantes para búsquedas científicas
- ✅ Fácil de integrar

## 📚 Notas Técnicas

- Las búsquedas se realizan usando `duckduckgo-search`
- Por defecto retorna 5 resultados (configurable)
- Los resultados incluyen título, descripción y URL
- Researcher Tool usa LLM para sintetizar resultados con contexto científico

## 🧠 Aprendizaje Continuo

**¡NUEVO!** El sistema ahora aprende automáticamente de cada búsqueda realizada:

### ¿Cómo funciona?

1. **Búsqueda Web (`web_search_tool`)**:
   - Realiza la búsqueda en DuckDuckGo
   - Combina todos los resultados en un documento estructurado
   - Divide el documento en chunks usando `Chunker`
   - Agrega los chunks al vector store (Pinecone) con identificador único
   - Los resultados quedan disponibles para futuras búsquedas semánticas

2. **Investigador (`researcher_tool`)**:
   - Realiza búsqueda web (que ya aprende automáticamente)
   - Sintetiza los resultados con contexto científico usando LLM
   - **También agrega la síntesis al vector store**
   - Esto permite que el sistema recuerde tanto los resultados crudos como las síntesis

### Beneficios

- ✅ **Memoria persistente**: El sistema recuerda información de búsquedas anteriores
- ✅ **Mejora continua**: Cada búsqueda enriquece la base de conocimiento
- ✅ **Búsquedas semánticas mejoradas**: Los resultados aprendidos aparecen en búsquedas similares
- ✅ **Contexto acumulativo**: El sistema puede relacionar información de diferentes búsquedas

### Ejemplo de Flujo

```
Usuario: "¿Qué es un agujero negro?"

1. Sistema busca en DuckDuckGo
2. Obtiene resultados y los muestra al usuario
3. **Automáticamente agrega resultados al vector store**
4. **Agrega síntesis científica al vector store**

Usuario (más tarde): "Explícame sobre los agujeros negros"

1. Sistema busca en vector store (encuentra información de búsqueda anterior)
2. Puede combinar información del vector store con nueva búsqueda si es necesario
3. Proporciona respuesta más completa y contextualizada
```

### Identificadores de Documentos

Los documentos de búsqueda se identifican con:
- `web_search_YYYYMMDD_HHMMSS_hash`: Para resultados de búsqueda directa
- `web_research_synthesis_YYYYMMDD_HHMMSS_hash`: Para síntesis científicas

Esto permite rastrear cuándo se realizó cada búsqueda y qué información se aprendió.

### Control del Aprendizaje

Puedes controlar si el sistema aprende o no usando el parámetro `learn`:

```python
# Aprender (por defecto)
web_search_tool("agujeros negros", learn=True)

# No aprender
web_search_tool("agujeros negros", learn=False)
```

Por defecto, `learn=True` para que el sistema siempre mejore su conocimiento.

