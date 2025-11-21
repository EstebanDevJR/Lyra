# 📚 Documentación Técnica del Backend

Este directorio contiene la documentación técnica detallada del sistema backend de Lyra.

## 📖 Índice de Documentación

- **[README.md](README.md)** (este archivo) - Implementación LangGraph y arquitectura
- **[AGENTS_README.md](AGENTS_README.md)** - Documentación detallada de todos los agentes
- **[CONNECTION.md](CONNECTION.md)** - Guía de conexión y configuración
- **[TOOLS_VERIFICATION.md](TOOLS_VERIFICATION.md)** - Verificación de herramientas
- **[WEB_SEARCH.md](WEB_SEARCH.md)** - Documentación de búsqueda web

---

# LangGraph Implementation - Multi-Agent System

Esta implementación utiliza **LangGraph** para orquestar el sistema multiagente con patrones de diseño modernos.

## 🏗️ Arquitectura

### Patrones de Diseño Implementados

1. **Singleton Pattern** (`SupervisorGraph`, `ToolFactory`)
   - Garantiza una única instancia del supervisor y factory
   - Reduce consumo de memoria y mejora rendimiento

2. **Factory Pattern** (`ToolFactory`)
   - Centraliza la creación y gestión de herramientas
   - Facilita agregar nuevas herramientas dinámicamente

3. **Observer Pattern** (`Observer`, `Subject`)
   - Sistema de logging y métricas desacoplado
   - Permite agregar múltiples observadores (logs, métricas, monitoreo)

4. **State Pattern** (`AgentState`)
   - Estado tipado y estructurado para el flujo de trabajo
   - Facilita debugging y seguimiento

## 📁 Estructura de Archivos

```
agents/graph/
├── __init__.py           # Exports principales
├── state.py              # Definición del estado (State Pattern)
├── tool_factory.py       # Factory para herramientas (Factory + Singleton)
├── observer.py           # Sistema de observadores (Observer Pattern)
└── supervisor_graph.py   # Grafo principal (Singleton + LangGraph)
```

## 🚀 Uso

### Uso Básico

```python
from agents.graph.supervisor_graph import create_supervisor_graph, process_query

# Crear instancia del grafo (Singleton)
graph = create_supervisor_graph()

# Procesar consulta
result = process_query("Analiza un documento sobre agujeros negros")
print(result)
```

### Uso Avanzado con Streaming

```python
from agents.graph.supervisor_graph import SupervisorGraph
from langchain_core.messages import HumanMessage

graph = SupervisorGraph()

# Stream de resultados
for state in graph.stream("Analiza un documento"):
    print(state)
```

### Agregar Observadores Personalizados

```python
from agents.graph.observer import Observer
from agents.graph.supervisor_graph import SupervisorGraph

class CustomObserver(Observer):
    def update(self, event: str, data: dict):
        # Tu lógica personalizada
        print(f"Event: {event}, Data: {data}")

graph = SupervisorGraph()
graph.attach(CustomObserver())
```

### Obtener Métricas

```python
from agents.graph.supervisor_graph import SupervisorGraph
from agents.graph.observer import MetricsObserver

graph = SupervisorGraph()

# Procesar consulta
result = graph.invoke("Consulta de ejemplo")

# Obtener métricas
metrics_observer = None
for obs in graph._observers:
    if isinstance(obs, MetricsObserver):
        metrics_observer = obs
        break

if metrics_observer:
    metrics = metrics_observer.get_metrics()
    print(f"Tool calls: {metrics['tool_calls']}")
    print(f"Errors: {metrics['errors']}")
```

## 🔄 Migración desde LangChain

El código mantiene compatibilidad hacia atrás:

```python
from agents.supervisor_agent import create_supervisor_agent, process_query

# Usar LangGraph (recomendado, por defecto)
agent = create_supervisor_agent(use_langgraph=True)
result = process_query("query", use_langgraph=True)

# Usar LangChain legacy (compatibilidad)
agent = create_supervisor_agent(use_langgraph=False)
result = process_query("query", use_langgraph=False)
```

## ✨ Ventajas de LangGraph

1. **Flujo de Trabajo Explícito**: El grafo define claramente el flujo de ejecución
2. **Estado Persistente**: El estado se mantiene a través de los nodos
3. **Debugging Mejorado**: Más fácil seguir el flujo de ejecución
4. **Escalabilidad**: Fácil agregar nuevos nodos y rutas
5. **Observabilidad**: Sistema integrado de logging y métricas

## 📊 Componentes Principales

### AgentState
Estado tipado que contiene:
- `messages`: Mensajes de la conversación
- `current_step`: Paso actual en el workflow
- `tool_results`: Resultados de herramientas ejecutadas
- `context`: Contexto adicional
- `metadata`: Metadatos de ejecución
- `next_agent`: Próximo agente a ejecutar (opcional)

### ToolFactory
- Registra todas las herramientas disponibles
- Proporciona acceso centralizado a herramientas
- Permite registro dinámico de nuevas herramientas

### Observer System
- `LoggingObserver`: Logs a consola/archivo
- `MetricsObserver`: Tracking de métricas (llamadas, errores, tiempos)
- `Subject`: Notifica a todos los observadores

### SupervisorGraph
- Construye y ejecuta el grafo de LangGraph
- Integra todas las herramientas
- Maneja errores y logging
- Proporciona métricas de ejecución

## 🔧 Extensión

### Agregar Nueva Herramienta

```python
from agents.graph.tool_factory import ToolFactory

factory = ToolFactory()
factory.register_tool(
    name="MiNuevaHerramienta",
    func=mi_funcion,
    description="Descripción de la herramienta"
)
```

### Agregar Nuevo Nodo al Grafo

```python
# En supervisor_graph.py
def _build_graph(self):
    workflow = StateGraph(AgentState)
    
    # Agregar nuevo nodo
    workflow.add_node("mi_nuevo_nodo", self._mi_nuevo_nodo)
    
    # Conectar nodos
    workflow.add_edge("supervisor", "mi_nuevo_nodo")
    workflow.add_edge("mi_nuevo_nodo", "agent")
    
    return workflow.compile()
```

## 📝 Notas

- El sistema usa **Singleton** para `SupervisorGraph` y `ToolFactory`
- Los observadores se pueden agregar/remover dinámicamente
- El estado se mantiene a través de toda la ejecución
- Compatible con la implementación legacy de LangChain

