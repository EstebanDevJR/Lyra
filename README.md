# Lyra - Sistema de Chatbot Inteligente

Lyra es un sistema avanzado de chatbot que utiliza múltiples agentes especializados para proporcionar respuestas precisas y contextualizadas. El sistema incluye un backend en Python con FastAPI y un frontend en Next.js con capacidades de llamada en tiempo real usando OpenAI Realtime API.

## 🚀 Características

- **Arquitectura Multi-Agente**: Sistema distribuido con agentes especializados (supervisor, contexto, investigador, respondedor, etc.)
- **Búsqueda Web Inteligente**: Integración con DuckDuckGo para búsquedas contextualizadas
- **Procesamiento de Documentos**: OCR y procesamiento de PDFs
- **Base de Conocimiento Vectorial**: Almacenamiento y recuperación semántica de información
- **Modo Llamada en Tiempo Real**: Conversación de voz usando OpenAI Realtime API
- **Interfaz Moderna**: Frontend construido con Next.js, React y Three.js

## 📁 Estructura del Proyecto

```
Lucy/
├── Backend/          # Backend en Python con FastAPI
│   ├── src/
│   │   ├── agents/   # Agentes especializados
│   │   ├── core/     # Funcionalidades principales
│   │   └── interface/ # API y endpoints
│   └── requirements.txt
├── Chatbot/          # Frontend en Next.js
│   ├── app/          # Páginas y rutas
│   ├── components/   # Componentes React
│   └── lib/          # Utilidades y clientes
└── README.md
```

## 🛠️ Instalación

### Backend

1. Navega al directorio Backend:
```bash
cd Backend
```

2. Crea un entorno virtual:
```bash
python -m venv venv
```

3. Activa el entorno virtual:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

4. Instala las dependencias:
```bash
pip install -r requirements.txt
```

5. Configura las variables de entorno (crea un archivo `.env`):
```env
OPENAI_API_KEY=tu_api_key_aqui
LANGCHAIN_API_KEY=tu_langchain_key_aqui
```

6. Ejecuta el servidor:
```bash
uvicorn src.main:app --reload
```

### Frontend

1. Navega al directorio Chatbot:
```bash
cd Chatbot
```

2. Instala las dependencias:
```bash
npm install
# o
pnpm install
```

3. Ejecuta el servidor de desarrollo:
```bash
npm run dev
# o
pnpm dev
```

## 👤 Autor

EstebanDevJR


