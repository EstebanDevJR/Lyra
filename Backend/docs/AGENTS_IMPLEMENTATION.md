# 🤖 Implementación de Agentes Avanzados para Lyra

Este documento detalla la implementación de los nuevos agentes especializados para el sistema Lyra.

---

## 📋 Agentes Implementados

### 1. 🧩 Planner Agent (`planner_agent.py`)

**Función**: Divide tareas complejas en subtareas usando Task Decomposition.

**Características**:
- Descomposición estructurada de tareas
- Identificación de dependencias entre subtareas
- Estimación de complejidad
- Generación de planes de ejecución ordenados

**Uso**:
```python
from agents.planner_agent import planner_agent_tool

plan = planner_agent_tool(
    "Analizar un artículo sobre agujeros negros y generar un resumen",
    available_tools=["Extractor", "Analyzer", "Summarizer"]
)
```

**Salida**: Plan estructurado con subtareas, herramientas asignadas y orden de ejecución.

---

### 2. 🔧 Tool Agent (`tool_agent.py`)

**Función**: Usa herramientas externas (APIs, calculadoras, visualizaciones).

**Herramientas soportadas**:
- **NASA API**: Consulta Astronomy Picture of the Day
- **Calculadora Orbital**: Calcula parámetros orbitales usando leyes de Kepler
- **Calculadora de Agujeros Negros**: Calcula radio de Schwarzschild, temperatura de Hawking, etc.

**Uso**:
```python
from agents.tool_agent import tool_agent_tool

# Calcular parámetros orbitales
result = tool_agent_tool(
    "orbital_calc",
    '{"mass": 1.989e30, "distance": 1.496e11, "period": 31536000}'
)

# Calcular parámetros de agujero negro
result = tool_agent_tool(
    "black_hole_calc",
    '{"mass": 6.5e9}'
)
```

---

### 3. 🧠 Retraining Agent (mejorado en `additional_tools.py`)

**Función**: Detecta automáticamente nuevos datos relevantes y actualiza embeddings.

**Mejoras**:
- **Auto-detección**: Extrae automáticamente información científica relevante
- **Filtrado inteligente**: Elimina información irrelevante y repeticiones
- **Integración con ContextManager**: Almacena métricas de re-entrenamiento

**Uso**:
```python
from agents.additional_tools import retrainer_tool

result = retrainer_tool(
    new_data="Nuevo descubrimiento sobre exoplanetas...",
    auto_detect=True  # Extrae automáticamente información relevante
)
```

---

### 4. 💬 Dialogue Agent (`dialogue_agent.py`)

**Función**: Mejora la interacción natural y emocional con el usuario.

**Personalidades disponibles**:
- `scientific`: Formal y preciso
- `friendly`: Amigable y accesible
- `enthusiastic`: Entusiasta y apasionado
- `professional`: Profesional y conciso

**Características**:
- Detección de emociones del usuario
- Ajuste de tono según contexto
- Mejora de transiciones naturales

**Uso**:
```python
from agents.dialogue_agent import dialogue_agent_tool

enhanced = dialogue_agent_tool(
    content="Los agujeros negros son objetos fascinantes...",
    personality="enthusiastic",
    context='{"is_first_message": true, "user_emotion": "curious"}'
)
```

---

### 5. 📈 Evaluator Agent (`evaluator_agent.py`)

**Función**: Mide rendimiento de otros agentes (precision, recall, latencia).

**Métricas**:
- Precisión (0-1)
- Completitud (0-1)
- Relevancia (0-1)
- Tiempo de ejecución
- Throughput

**Uso**:
```python
from agents.evaluator_agent import evaluator_agent_tool

metrics = evaluator_agent_tool(
    agent_name="Analyzer",
    input_data="Consulta sobre agujeros negros",
    output_data="Respuesta del agente...",
    expected_output="Respuesta esperada...",
    execution_time=2.5
)

# Obtener estadísticas de un agente
from agents.evaluator_agent import EvaluatorAgent
agent = EvaluatorAgent()
stats = agent.get_agent_statistics("Analyzer")
```

---

### 6. 🧰 Knowledge Graph Agent (`knowledge_graph_agent.py`)

**Función**: Construye y consulta relaciones entre conceptos (RAG + grafos).

**Operaciones**:
- `build`: Construye grafo desde texto
- `query`: Consulta entidades y relaciones
- `find_path`: Encuentra rutas entre entidades

**Características**:
- Extracción automática de entidades y relaciones
- Almacenamiento persistente en contexto
- Integración con vector store para búsqueda semántica

**Uso**:
```python
from agents.knowledge_graph_agent import knowledge_graph_agent_tool

# Construir grafo
result = knowledge_graph_agent_tool(
    text="Los agujeros negros tienen un horizonte de eventos...",
    operation="build"
)

# Consultar entidad
result = knowledge_graph_agent_tool(
    text="agujero negro",
    operation="query",
    depth=2
)

# Encontrar ruta
result = knowledge_graph_agent_tool(
    text="agujero negro, singularidad",
    operation="find_path",
    source="agujero negro",
    target="singularidad"
)
```

---

### 7. 🌍 API Integration Agent (`api_integration_agent.py`)

**Función**: Consulta servicios externos (NASA, ESA, ADS, Wikipedia).

**APIs soportadas**:
- **NASA APOD**: Astronomy Picture of the Day
- **NASA NEO**: Near Earth Objects
- **Wikipedia**: Búsqueda de temas astronómicos
- **ADS**: Astrophysics Data System (requiere autenticación)

**Uso**:
```python
from agents.api_integration_agent import api_integration_agent_tool

# NASA APOD
result = api_integration_agent_tool("nasa_apod", "today")

# Wikipedia
result = api_integration_agent_tool("wikipedia", "agujero negro", lang="es")

# NASA NEO
result = api_integration_agent_tool(
    "nasa_neo",
    "2024-01-01",
    start_date="2024-01-01",
    end_date="2024-01-07"
)
```

---

## 🔗 Integración en el Sistema

Todos los agentes están integrados en el `ToolFactory` y disponibles para el `SupervisorGraph`:

```python
from agents.graph.supervisor_graph import SupervisorGraph

graph = SupervisorGraph()
result = graph.invoke("Analiza este artículo sobre agujeros negros")
```

El supervisor puede usar automáticamente estos agentes según la necesidad de la tarea.

---

## 📊 Beneficios

1. **Planner**: Permite manejar tareas complejas de forma estructurada
2. **Tool Agent**: Añade capacidades de cálculo y visualización
3. **Retraining**: Aprendizaje continuo automático
4. **Dialogue**: Mejor experiencia de usuario
5. **Evaluator**: Monitoreo y optimización del sistema
6. **Knowledge Graph**: Relaciones semánticas entre conceptos
7. **API Integration**: Conocimiento dinámico y actualizado

---

## 🚀 Próximos Pasos

- [ ] Implementar visualización de grafos de conocimiento
- [ ] Añadir más APIs (ESA, SIMBAD, etc.)
- [ ] Mejorar detección de emociones del usuario
- [ ] Implementar métricas avanzadas de evaluación
- [ ] Añadir soporte para simulaciones orbitales visuales

---

**Última actualización**: Implementación completa de todos los agentes avanzados.

