# 🌠 Lyra: Asistente de Análisis Científico Astronómico

**Lyra** es un asistente de inteligencia artificial diseñado para analizar, resumir y contextualizar información científica sobre el espacio — en especial sobre **agujeros negros, galaxias y fenómenos astrofísicos**.  
El sistema integra OCR, embeddings, búsqueda semántica y una arquitectura **multiagente en LangChain**, simulando el flujo de trabajo de un investigador digital.

---

## 🧩 Objetivo del proyecto

Este proyecto forma parte del módulo final de **Introducción a la Inteligencia Artificial**, y su propósito es demostrar la comprensión práctica de los siguientes conceptos:

- Extracción y procesamiento de datos (OCR, texto, PDFs, imágenes)
- Segmentación (*chunking*) y embeddings usando OpenAI text-embedding-3-small
- Similitud semántica y bases vectoriales (Pinecone)
- Arquitectura de agentes múltiples en LangChain
- Interacción con modelos LLM de OpenAI

---

## 🚀 Descripción general

**Lyra** actúa como un **investigador astronómico digital**.  
El usuario puede subir artículos, papers o imágenes escaneadas, y Lyra:

1. Extrae el texto (OCR si es necesario)  
2. Limpia y estructura el contenido  
3. Genera *embeddings* para análisis semántico  
4. Busca fragmentos relevantes en la base vectorial  
5. Resume, traduce o amplía el contenido  
6. Calcula variables físicas si es necesario  
7. Genera una respuesta final coherente y validada  

Todo esto es orquestado por un **Supervisor Agent**, que decide qué herramientas (agentes) activar según la solicitud del usuario.

---

## 🧠 Arquitectura Multiagente

Lyra utiliza una arquitectura modular basada en **LangGraph - LangChain Agents + Tools**, donde cada agente cumple un rol definido dentro del pipeline de procesamiento y análisis.

### 🔹 Agentes principales

| Agente | Función | Descripción |
|---------|----------|-------------|
| 🧾 **Extractor** | OCR / lectura | Extrae texto desde PDFs o imágenes |
| 🧹 **Cleaner** | Limpieza de texto | Elimina ruido, caracteres erróneos y símbolos |
| 🔍 **Analyzer** | Búsqueda semántica | Analiza embeddings y encuentra fragmentos relevantes |
| 📊 **Summarizer** | Resumen | Sintetiza información en lenguaje natural |
| 💬 **Responder** | Respuesta final | Redacta la respuesta final de Lyra |
| 🧠 **Contextualizer** | Contexto adicional | Agrega información de fondo sobre los hallazgos |
| 🔎 **Validator** | Validación | Verifica la coherencia y exactitud científica |

### 🔹 Agentes complementarios

| Agente | Función | Descripción |
|---------|----------|-------------|
| 🧮 **Computation** | Cálculos físicos | Calcula masas, radios, distancias, etc. |
| 📚 **Researcher** | Investigación externa | Consulta APIs (NASA, arXiv, Wikipedia) |
| 🧩 **Planner** | Planificación | Decide la secuencia óptima de acciones |
| 💾 **Memory** | Memoria | Almacena contexto de interacción |
| 🧰 **KnowledgeGraph** | Relaciones conceptuales | Crea conexiones entre conceptos científicos |

---

### 📚 Ejemplo de uso

Entrada:

"Subo una imagen del artículo del EHT sobre la primera fotografía de un agujero negro."

Salida (Lyra):

"El artículo describe los resultados del Event Horizon Telescope (EHT) en 2019, donde se obtuvo la primera imagen del agujero negro M87*.
Se estima su masa en 6.5 mil millones de masas solares.
Esta observación confirma las predicciones de la relatividad general en entornos extremos."

---

## ⚙️ Configuración e Instalación

### Requisitos

- Python 3.8+
- Cuenta de OpenAI (para embeddings y LLM)
- Cuenta de Pinecone (para vector store)

### Instalación

1. Clona el repositorio y navega al directorio `Backend`:
```bash
cd Backend
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

### Variables de Entorno

Crea un archivo `.env` en el directorio `Backend` con las siguientes variables:

```env
# OpenAI (requerido)
OPENAI_API_KEY=tu_clave_openai_aqui

# Pinecone (requerido)
PINECONE_API_KEY=tu_clave_pinecone_aqui
PINECONE_REGION=us-east-1  # Región AWS para el índice serverless (opcional, por defecto: us-east-1)
PINECONE_INDEX_NAME=lyra-vectorstore  # Nombre del índice (opcional, por defecto: lyra-vectorstore)

# AWS (opcional, solo si usas Textract para OCR de imágenes y PDFs escaneados)
# Sin esto, solo funcionará la extracción de texto de PDFs legibles (PyPDF2)
AWS_ACCESS_KEY_ID=tu_clave_aws_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_aws_aqui
AWS_REGION=us-east-1
```

### Configuración de Pinecone

1. Crea una cuenta en [Pinecone](https://www.pinecone.io/)
2. Obtén tu API key desde el dashboard de Pinecone
3. El índice se creará automáticamente la primera vez que ejecutes la aplicación
4. El índice usa embeddings de **text-embedding-3-small** de OpenAI (1536 dimensiones)

### Ejecutar la API

```bash
python src/main.py --port 8000
```

La API estará disponible en `http://localhost:8000`

### Ejecutar con Uvicorn (Recomendado)

```bash
uvicorn src.main:app --reload --port 8000
```

### Verificar Instalación

```bash
# Verificar que el servidor responde
curl http://localhost:8000/health
```

---

## 🔌 API Endpoints

### Consultas

- **POST** `/api/query` - Procesar consulta de texto
  ```json
  {
    "query": "¿Qué es un agujero negro?",
    "session_id": "opcional"
  }
  ```

- **POST** `/api/upload` - Subir y procesar documentos
  ```bash
  curl -X POST "http://localhost:8000/api/upload" \
    -F "file=@documento.pdf" \
    -F "query=Analiza este documento"
  ```

### Realtime API

- **POST** `/api/realtime/connect` - Conectar a OpenAI Realtime API
- **WebSocket** `/api/realtime/ws` - Conexión WebSocket para streaming

### Utilidades

- **GET** `/health` - Estado del servidor
- **GET** `/docs` - Documentación interactiva (Swagger UI)

---

## 🧠 Arquitectura LangGraph

El sistema utiliza **LangGraph** para orquestar el flujo de trabajo multiagente:

### Componentes Principales

- **SupervisorGraph**: Grafo principal que coordina los agentes
- **AgentState**: Estado tipado que se mantiene a través del flujo
- **ToolFactory**: Factory para crear y gestionar herramientas
- **ContextManager**: Gestión de contexto compartido
- **ResourceManager**: Gestión de recursos (VectorStore, LLMs)

**Documentación técnica**: Ver [docs/README.md](docs/README.md)

---

## 📚 Documentación Adicional

**Toda la documentación técnica está centralizada en el directorio `docs/` de la raíz del proyecto:**

- **[docs/README.md](../docs/README.md)** - Índice completo de documentación
- **[docs/backend/langgraph.md](../docs/backend/langgraph.md)** - Implementación LangGraph
- **[docs/backend/agents.md](../docs/backend/agents.md)** - Documentación detallada de agentes
- **[docs/backend/connection.md](../docs/backend/connection.md)** - Conexión Frontend-Backend
- **[docs/backend/tools.md](../docs/backend/tools.md)** - Verificación de herramientas
- **[docs/backend/web-search.md](../docs/backend/web-search.md)** - Búsqueda web con DuckDuckGo

---

## 🔧 Desarrollo

### Estructura de Código

```
src/
├── agents/              # Agentes especializados
│   ├── graph/          # Implementación LangGraph
│   │   ├── supervisor_graph.py
│   │   ├── state.py
│   │   └── tool_factory.py
│   └── *.py            # Agentes individuales
├── core/               # Funcionalidades principales
│   ├── embeddings.py
│   ├── vectorstore.py
│   └── chunking.py
├── interface/          # API y endpoints
│   ├── api.py
│   └── realtime_api.py
└── main.py            # Punto de entrada
```

### Agregar un Nuevo Agente

1. Crea el archivo del agente en `src/agents/`
2. Implementa las funciones de herramienta
3. Registra el agente en `supervisor_graph.py`
4. Agrega la herramienta en `tool_factory.py`

---

## 🐛 Troubleshooting

### Error: "Pinecone index not found"
- Verifica que `PINECONE_API_KEY` esté configurada
- El índice se crea automáticamente en el primer uso

### Error: "OpenAI API key not found"
- Verifica que `OPENAI_API_KEY` esté en el archivo `.env`

### Error: "Module not found"
- Asegúrate de estar en el entorno virtual: `source venv/bin/activate`
- Reinstala dependencias: `pip install -r requirements.txt`

---

## 📝 Notas

- El sistema usa **Singleton** para recursos compartidos
- Los embeddings usan `text-embedding-3-small` (1536 dimensiones)
- El vector store se inicializa de forma lazy (solo cuando se necesita)
- Compatible con Python 3.8+