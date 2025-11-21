# 🔗 Conexión Frontend-Backend

Esta guía explica cómo conectar el frontend (Next.js) con el backend (FastAPI).

## 📋 Requisitos Previos

1. Backend ejecutándose en `http://localhost:8000`
2. Frontend ejecutándose en `http://localhost:3000` (o el puerto configurado)

## 🚀 Configuración

### Backend

1. Asegúrate de tener todas las dependencias instaladas:
```bash
cd Backend
pip install -r requirements.txt
```

2. Configura las variables de entorno en un archivo `.env`:
```env
OPENAI_API_KEY=tu_clave_openai
PINECONE_API_KEY=tu_clave_pinecone
PINECONE_REGION=us-east-1
PINECONE_INDEX_NAME=lyra-vectorstore
```

3. Inicia el servidor:
```bash
python src/main.py --port 8000
```

El servidor estará disponible en `http://localhost:8000`
- API: `http://localhost:8000`
- Documentación: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend

1. Configura la URL del backend (opcional, por defecto usa `http://localhost:8000`):
   
   Crea un archivo `.env.local` en el directorio `Chatbot`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

2. Instala dependencias e inicia el servidor:
```bash
cd Chatbot
npm install
npm run dev
```

## 🔌 Endpoints Disponibles

### POST `/query`
Procesa una consulta usando el agente supervisor (LangGraph).

**Request:**
```json
{
  "query": "¿Qué es un agujero negro?",
  "file_path": "opcional/ruta/archivo.pdf"
}
```

**Response:**
```json
{
  "response": "Respuesta del agente...",
  "status": "success"
}
```

### POST `/upload`
Sube un archivo (PDF o imagen) y extrae texto.

**Request:**
- Form-data con campo `file`

**Response:**
```json
{
  "file_path": "/path/to/file",
  "extracted_text": "Texto extraído...",
  "status": "success",
  "message": "Archivo procesado exitosamente"
}
```

### GET `/health`
Verifica el estado del servidor.

**Response:**
```json
{
  "status": "healthy",
  "openai_configured": true
}
```

## 🧪 Prueba la Conexión

1. Inicia el backend:
```bash
cd Backend
python src/main.py
```

2. En otra terminal, inicia el frontend:
```bash
cd Chatbot
npm run dev
```

3. Abre `http://localhost:3000/chat` en tu navegador

4. Prueba enviando un mensaje o subiendo un archivo

## 🐛 Solución de Problemas

### Error: "Failed to fetch"
- Verifica que el backend esté ejecutándose en `http://localhost:8000`
- Verifica que CORS esté habilitado en el backend (ya está configurado)
- Verifica la URL en `Chatbot/lib/api.ts` o en `.env.local`

### Error: "OPENAI_API_KEY no está configurada"
- Asegúrate de tener un archivo `.env` en el directorio `Backend`
- Verifica que la variable `OPENAI_API_KEY` esté configurada

### Error: "PINECONE_API_KEY environment variable is required"
- Configura `PINECONE_API_KEY` en el archivo `.env` del backend
- Obtén tu API key desde [Pinecone](https://www.pinecone.io/)

### El frontend no se conecta al backend
- Verifica que ambos servidores estén ejecutándose
- Verifica los logs del backend para ver errores
- Abre las herramientas de desarrollador del navegador (F12) y revisa la consola

## 📝 Notas

- El backend usa **LangGraph** por defecto para orquestar los agentes
- El sistema está configurado con CORS para permitir conexiones desde cualquier origen (en producción, restringe esto)
- Los archivos subidos se guardan en `Backend/src/data/raw/`
- El vector store usa **Pinecone** para almacenar embeddings

