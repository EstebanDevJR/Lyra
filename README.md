# 🌌 Lyra - Asistente de Análisis Científico Astronómico

**Lyra** es un sistema avanzado de inteligencia artificial diseñado para analizar, resumir y contextualizar información científica sobre el espacio — especialmente sobre **agujeros negros, galaxias y fenómenos astrofísicos**. El sistema integra OCR, embeddings, búsqueda semántica y una arquitectura **multiagente en LangGraph**, simulando el flujo de trabajo de un investigador digital.

---

## 🚀 Características Principales

### 🧠 Arquitectura Multi-Agente
- **Sistema distribuido** con agentes especializados (supervisor, contexto, investigador, respondedor, etc.)
- **Orquestación con LangGraph** para flujos de trabajo complejos
- **Herramientas modulares** y extensibles
- **Gestión de contexto** compartido entre agentes

### 🔍 Capacidades de Análisis
- **Búsqueda Web Inteligente**: Integración con DuckDuckGo para búsquedas contextualizadas
- **Procesamiento de Documentos**: OCR y procesamiento de PDFs (PyPDF2 y AWS Textract)
- **Base de Conocimiento Vectorial**: Almacenamiento y recuperación semántica usando Pinecone
- **Análisis Semántico**: Búsqueda por similitud usando embeddings de OpenAI

### 💬 Interfaz de Usuario
- **Chat Interactivo**: Conversación de texto con respuestas contextualizadas
- **Modo Llamada en Tiempo Real**: Conversación de voz usando OpenAI Realtime API
- **Dashboard Astronómico**: Visualización de noticias, imágenes, papers y alertas astronómicas
- **Interfaz Moderna**: Frontend construido con Next.js, React y Three.js

### 🌠 Integraciones Astronómicas
- **NASA APOD**: Imagen astronómica del día
- **ArXiv**: Papers científicos recientes con resúmenes generados por IA
- **Noticias Espaciales**: Agregación de noticias astronómicas
- **Alertas Astronómicas**: Objetos cercanos a la Tierra (NEOs) y eventos espaciales

---

## 📁 Estructura del Proyecto

```
Lucy/
├── Backend/                    # Backend en Python con FastAPI
│   ├── src/
│   │   ├── agents/            # Agentes especializados
│   │   │   ├── graph/        # Implementación LangGraph
│   │   │   └── *.py          # Agentes individuales
│   │   ├── core/             # Funcionalidades principales
│   │   │   ├── embeddings.py
│   │   │   ├── vectorstore.py
│   │   │   └── ...
│   │   ├── interface/        # API y endpoints
│   │   │   ├── api.py
│   │   │   └── realtime_api.py
│   │   └── main.py           # Punto de entrada
│   ├── docs/                 # Documentación del backend
│   ├── requirements.txt
│   └── README.md
│
├── Chatbot/                   # Frontend en Next.js
│   ├── app/                  # Páginas y rutas
│   │   ├── api/              # API Routes (proxy para n8n)
│   │   ├── chat/             # Página de chat
│   │   └── page.tsx          # Landing page
│   ├── components/           # Componentes React
│   │   ├── astronomy/        # Componentes astronómicos
│   │   ├── news/             # Componentes de noticias
│   │   └── ui/               # Componentes UI reutilizables
│   ├── lib/                  # Utilidades y clientes
│   ├── N8N_WORKFLOWS_GUIDE.md
│   ├── SETUP.md
│   └── package.json
│
└── README.md                  # Este archivo
```

---

## 🛠️ Instalación y Configuración

### Prerrequisitos

- **Python 3.8+** (para Backend)
- **Node.js 18+** (para Frontend)
- **Cuenta de OpenAI** (para embeddings y LLM)
- **Cuenta de Pinecone** (para vector store)
- **n8n** (opcional, para workflows astronómicos)
- **NASA API Key** (opcional, para datos astronómicos)

### 1. Backend

#### Instalación

```bash
cd Backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

#### Variables de Entorno

Crea un archivo `.env` en el directorio `Backend`:

```env
# OpenAI (requerido)
OPENAI_API_KEY=tu_clave_openai_aqui

# Pinecone (requerido)
PINECONE_API_KEY=tu_clave_pinecone_aqui
PINECONE_REGION=us-east-1
PINECONE_INDEX_NAME=lyra-vectorstore

# AWS (opcional, solo para OCR avanzado)
AWS_ACCESS_KEY_ID=tu_clave_aws_aqui
AWS_SECRET_ACCESS_KEY=tu_secret_aws_aqui
AWS_REGION=us-east-1

# LangSmith (opcional, para debugging)
LANGCHAIN_API_KEY=tu_langchain_key_aqui
```

#### Ejecutar el Servidor

```bash
# Desarrollo
uvicorn src.main:app --reload

# O usando el script
python src/main.py --port 8000
```

La API estará disponible en `http://localhost:8000`

**Documentación completa del Backend**: Ver [Backend/README.md](Backend/README.md)

---

### 2. Frontend

#### Instalación

```bash
cd Chatbot

# Instalar dependencias
npm install
# o
pnpm install
```

#### Variables de Entorno

Crea un archivo `.env.local` en el directorio `Chatbot`:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# n8n Webhooks (opcional)
NEXT_PUBLIC_N8N_NEWS_WEBHOOK=http://localhost:5678/webhook/news
NEXT_PUBLIC_N8N_ASTRONOMY_IMAGE_WEBHOOK=http://localhost:5678/webhook/astronomy-image
NEXT_PUBLIC_N8N_RESEARCH_PAPERS_WEBHOOK=http://localhost:5678/webhook/research-papers
NEXT_PUBLIC_N8N_ASTRO_ALERTS_WEBHOOK=http://localhost:5678/webhook/astro-alerts

# NASA API (opcional, para fallback)
NASA_API_KEY=tu_nasa_api_key_aqui
```

#### Ejecutar el Servidor de Desarrollo

```bash
npm run dev
# o
pnpm dev
```

El frontend estará disponible en `http://localhost:3000`

**Documentación completa del Frontend**: Ver [Chatbot/SETUP.md](Chatbot/SETUP.md)

---

### 3. n8n Workflows (Opcional)

Para habilitar las integraciones astronómicas (noticias, imágenes, papers, alertas), configura los workflows de n8n.

**Guía completa**: Ver [Chatbot/N8N_WORKFLOWS_GUIDE.md](Chatbot/N8N_WORKFLOWS_GUIDE.md)

---

## 🧠 Arquitectura Multi-Agente

Lyra utiliza una arquitectura modular basada en **LangGraph**, donde cada agente cumple un rol definido:

### Agentes Principales

| Agente | Función | Descripción |
|--------|---------|-------------|
| 🧾 **Extractor** | OCR / lectura | Extrae texto desde PDFs o imágenes |
| 🧹 **Cleaner** | Limpieza de texto | Elimina ruido, caracteres erróneos y símbolos |
| 🔍 **Analyzer** | Búsqueda semántica | Analiza embeddings y encuentra fragmentos relevantes |
| 📊 **Summarizer** | Resumen | Sintetiza información en lenguaje natural |
| 💬 **Responder** | Respuesta final | Redacta la respuesta final de Lyra |
| 🧠 **Contextualizer** | Contexto adicional | Agrega información de fondo sobre los hallazgos |
| 🔎 **Evaluator** | Validación | Verifica la coherencia y exactitud científica |

### Agentes Complementarios

| Agente | Función | Descripción |
|--------|---------|-------------|
| 🧮 **Tool Agent** | Cálculos físicos | Calcula masas, radios, distancias, etc. |
| 📚 **API Integration** | Investigación externa | Consulta APIs (NASA, arXiv, Wikipedia) |
| 🧩 **Planner** | Planificación | Decide la secuencia óptima de acciones |
| 💾 **Context Agent** | Memoria | Almacena contexto de interacción |
| 🧰 **Knowledge Graph** | Relaciones conceptuales | Crea conexiones entre conceptos científicos |

**Documentación detallada de agentes**: Ver [Backend/docs/AGENTS_README.md](Backend/docs/AGENTS_README.md)

---

## 📚 Ejemplo de Uso

### Entrada:
```
"Sube una imagen del artículo del EHT sobre la primera fotografía de un agujero negro."
```

### Salida (Lyra):
```
"El artículo describe los resultados del Event Horizon Telescope (EHT) en 2019, 
donde se obtuvo la primera imagen del agujero negro M87*. 
Se estima su masa en 6.5 mil millones de masas solares. 
Esta observación confirma las predicciones de la relatividad general 
en entornos extremos."
```

---

## 🔌 API Endpoints

### Backend (FastAPI)

- `POST /api/query` - Procesar consulta de texto
- `POST /api/upload` - Subir y procesar documentos
- `POST /api/realtime/connect` - Conectar a Realtime API
- `GET /health` - Estado del servidor

**Documentación completa de la API**: Ver [Backend/README.md](Backend/README.md)

### Frontend (Next.js API Routes)

- `GET /api/news` - Obtener noticias astronómicas (proxy a n8n)
- `GET /api/astronomy-image` - Imagen del día (proxy a n8n)
- `GET /api/research-papers` - Papers científicos (proxy a n8n)
- `GET /api/astro-alerts` - Alertas astronómicas (proxy a n8n)

---

## 🎨 Tecnologías Utilizadas

### Backend
- **Python 3.8+**
- **FastAPI** - Framework web
- **LangChain / LangGraph** - Framework de agentes
- **OpenAI** - LLM y embeddings
- **Pinecone** - Vector database
- **AWS Textract** - OCR avanzado
- **PyPDF2** - Extracción de PDFs

### Frontend
- **Next.js 16** - Framework React
- **TypeScript** - Tipado estático
- **React 19** - Biblioteca UI
- **Three.js** - Gráficos 3D
- **Tailwind CSS** - Estilos
- **shadcn/ui** - Componentes UI
- **OpenAI Realtime API** - Conversación de voz

### Integraciones
- **n8n** - Automatización de workflows
- **NASA API** - Datos astronómicos
- **ArXiv API** - Papers científicos
- **DuckDuckGo** - Búsqueda web

---

## 📖 Documentación Adicional

**Toda la documentación está centralizada en el directorio `docs/`:**

- **[docs/README.md](docs/README.md)** - Índice completo de documentación
- **[Backend/README.md](Backend/README.md)** - Guía rápida del backend
- **[Chatbot/SETUP.md](Chatbot/SETUP.md)** - Guía rápida del frontend

### Documentación Detallada

- **[docs/backend/agents.md](docs/backend/agents.md)** - Documentación de agentes
- **[docs/backend/langgraph.md](docs/backend/langgraph.md)** - Arquitectura LangGraph
- **[docs/backend/connection.md](docs/backend/connection.md)** - Conexión Frontend-Backend
- **[docs/frontend/n8n-workflows.md](docs/frontend/n8n-workflows.md)** - Workflows n8n

---

## 🚧 Estado del Proyecto

### Funcionalidades Implementadas
- ✅ Sistema multiagente con LangGraph
- ✅ Procesamiento de documentos (PDF, imágenes)
- ✅ Búsqueda semántica con Pinecone
- ✅ Interfaz de chat interactiva
- ✅ Integración con OpenAI Realtime API
- ✅ Dashboard astronómico
- ✅ Workflows n8n para datos astronómicos

---

## 🙏 Agradecimientos

Este proyecto utiliza la increíble animación de agujero negro creada por [MisterPrada](https://github.com/MisterPrada) en el repositorio [singularity](https://github.com/MisterPrada/singularity). La implementación utiliza Three.js, TSL (Three Shader Language) y WebGPU/WebGL para crear una visualización impresionante de un agujero negro.

**Repositorio original**: [MisterPrada/singularity](https://github.com/MisterPrada/singularity)  
**Demo en vivo**: [singularity.misterprada.com](https://singularity.misterprada.com)

---

## 👤 Autor

**EstebanDevJR**

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas.

---

## ⚠️ Notas Importantes

- Este proyecto requiere claves API de servicios externos (OpenAI, Pinecone, etc.)
- Algunas funcionalidades requieren configuración adicional (n8n, AWS)
- El proyecto está optimizado para desarrollo local
- Para producción, se recomienda revisar configuraciones de seguridad

