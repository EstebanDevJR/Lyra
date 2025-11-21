# 📚 Documentación de Agentes - Lyra

Este documento describe todos los agentes implementados en el sistema Lyra.

## 🎯 Agentes Principales

### 1. 🧾 Extractor Agent (`extractor_agent.py`)
**Función**: Extrae texto de PDFs e imágenes usando OCR.

**Funciones principales**:
- `extractor_tool(file_path, method='auto')`: Función principal de extracción
- `extract_from_image(image_path)`: Extrae texto de imágenes usando AWS Textract
- `extract_from_pdf(pdf_path, method='auto')`: Extrae texto de PDFs

**Métodos soportados**:
- `auto`: Para PDFs, intenta PyPDF2 primero (PDFs legibles), luego Textract si falla (PDFs escaneados). Para imágenes, usa Textract.
- `pypdf2`: Extracción nativa de texto de PDFs legibles (solo PDFs)
- `textract`: OCR usando AWS Textract para imágenes y PDFs escaneados (requiere credenciales AWS)

**Nota**: Las imágenes siempre usan AWS Textract. Los PDFs escaneados requieren Textract si PyPDF2 no puede extraer texto.

---

### 2. 🧹 Cleaner Agent (`cleaner_agent.py`)
**Función**: Limpia y normaliza texto extraído eliminando ruido y caracteres problemáticos.

**Funciones principales**:
- `cleaner_tool(text, aggressive=False)`: Limpieza básica o agresiva
- `normalize_scientific_text(text)`: Normaliza texto científico preservando notación científica
- `remove_noise(text)`: Elimina ruido específico de OCR

**Características**:
- Elimina espacios excesivos
- Normaliza puntuación
- Preserva notación científica (e.g., 1.5e-10)
- Opción de limpieza agresiva para textos muy ruidosos

---

### 3. 🔍 Analyzer Agent (`analyzer_agent.py`)
**Función**: Analiza contenido científico y realiza búsqueda semántica usando el vector store.

**Funciones principales**:
- `analyzer_tool(query, k=5, add_to_store=False, document_text=None)`: Búsqueda semántica
- `classify_document(text)`: Clasifica documentos por categoría astronómica
- `identify_key_concepts(text, top_k=5)`: Identifica conceptos clave

**Características**:
- Búsqueda semántica usando Pinecone
- Clasificación automática por temas
- Identificación de conceptos científicos importantes
- Integración con vector store para búsqueda de documentos similares

---

### 4. 📊 Summarizer Agent (`summarizer_agent.py`)
**Función**: Resume documentos científicos enfocándose en hallazgos clave.

**Funciones principales**:
- `summarizer_tool(text, max_length=None, focus="key findings")`: Resumen principal
- `summarize_sections(text)`: Resume secciones por separado

**Opciones de enfoque**:
- `key findings`: Hallazgos y descubrimientos principales
- `methods`: Metodología y técnicas
- `results`: Resultados y datos cuantitativos
- `general`: Resumen general

**Características**:
- Usa LLM para resúmenes de alta calidad
- Fallback a resumen por extracción si falla LLM
- Preserva terminología científica
- Responde en español

---

### 5. 💬 Responder Agent (`responder_agent.py`)
**Función**: Genera la respuesta final para el usuario combinando resultados de otras herramientas.

**Funciones principales**:
- `responder_tool(context, user_query=None, style="scientific")`: Genera respuesta final
- `format_response(results, user_query=None)`: Formatea múltiples resultados

**Estilos de respuesta**:
- `scientific`: Lenguaje científico formal
- `casual`: Lenguaje accesible manteniendo precisión
- `detailed`: Información comprehensiva
- `brief`: Respuesta concisa

**Características**:
- Combina contexto de múltiples herramientas
- Personalizable según estilo deseado
- Incluye valores específicos cuando están disponibles
- Estructura clara y conclusiones

---

### 6. 🧠 Context Agent (`context_agent.py`)
**Función**: Agrega información de contexto adicional sobre hallazgos científicos.

**Funciones principales**:
- `contextualizer_tool(text, topic=None)`: Agrega contexto general
- `add_historical_context(text)`: Agrega contexto histórico
- `add_theoretical_context(text)`: Agrega contexto teórico

**Características**:
- Busca información relacionada en el vector store
- Proporciona contexto histórico de descubrimientos
- Explica conceptos teóricos subyacentes
- Conecta con otros documentos relacionados

---

### 7. 📖 Reference Agent (`reference_agent.py`)
**Función**: Extrae y gestiona referencias bibliográficas, citas, DOIs y arXiv IDs.

**Funciones principales**:
- `reference_tool(text, operation="extract")`: Función principal
- `extract_doi(text)`: Extrae DOIs
- `extract_arxiv_id(text)`: Extrae IDs de arXiv
- `create_reference_list(text)`: Crea lista de referencias formateada

**Operaciones**:
- `extract`: Extrae referencias del texto
- `format`: Formatea referencias consistentemente
- `validate`: Valida completitud y formato
- `cite`: Genera cita para el documento

**Características**:
- Detección de múltiples formatos de referencias
- Extracción de DOIs y arXiv IDs
- Formateo en estilo APA
- Validación de referencias completas

---

## 🛠️ Herramientas Adicionales (`additional_tools.py`)

### Formatter Tool
Formatea texto en estructuras consistentes (párrafos, secciones, etc.)

### Classifier Tool
Clasifica documentos por categoría astronómica (agujeros negros, galaxias, etc.)

### Data Curator Tool
Organiza y cura datos extraídos para mejorar calidad de embeddings

### Knowledge Graph Tool
Construye grafos de conocimiento vinculando entidades científicas

### Researcher Tool
Realiza investigación externa usando APIs (NASA, arXiv, Wikipedia)
*Nota: Actualmente usa LLM como placeholder; se puede integrar con APIs reales*

### Translator Tool
Traduce texto científico preservando terminología técnica

### Computation Tool
Realiza cálculos físicos y matemáticos (masas, radios, distancias, etc.)

### Validator Tool
Valida precisión científica, consistencia de datos y coherencia textual

### Evaluator Tool
Evalúa calidad, completitud y corrección de resultados generados

### Planner Tool
Planifica tareas multi-paso y decide secuencia de herramientas a usar

### Retrainer Tool
Actualiza embeddings y reentrena modelos con nuevos datos
*Mejorado: Ahora actualiza el vector store real*

### Memory Tool
Almacena y recupera interacciones previas y contexto
*Mejorado: Incluye timestamps y operaciones delete/clear*

---

## 🎮 Supervisor Agent (`supervisor_agent.py`)

**Función**: Orquesta el sistema multiagente usando LangChain.

**Funciones principales**:
- `create_supervisor_agent()`: Crea e inicializa el agente supervisor
- `process_query(query, agent=None)`: Procesa consultas del usuario

**Características**:
- Integra todas las herramientas disponibles
- Usa modelo GPT-4o-mini para orquestación
- Manejo de errores de parsing
- Modo verbose para debugging

**Herramientas disponibles**: 19 herramientas en total
1. Extractor
2. Cleaner
3. Formatter
4. Analyzer
5. Classifier
6. DataCurator
7. KnowledgeGraph
8. Researcher
9. APIIntegrator
10. Summarizer
11. Translator
12. Computation
13. Validator
14. Evaluator
15. Planner
16. Retrainer
17. Memory
18. Responder
19. Reference

---

## 📦 Estructura de Módulos

```
agents/
├── __init__.py              # Exports principales
├── extractor_agent.py      # Extracción OCR
├── cleaner_agent.py         # Limpieza de texto
├── analyzer_agent.py        # Análisis semántico
├── summarizer_agent.py      # Resumen de documentos
├── responder_agent.py       # Respuesta final
├── context_agent.py         # Contexto adicional
├── reference_agent.py      # Gestión de referencias
├── additional_tools.py       # Herramientas complementarias
├── supervisor_agent.py     # Orquestador principal
└── AGENTS_README.md         # Esta documentación
```

---

## 🚀 Uso Básico

```python
from agents.supervisor_agent import create_supervisor_agent, process_query

# Crear agente supervisor
agent = create_supervisor_agent()

# Procesar consulta
result = process_query("Analiza un documento sobre agujeros negros")
print(result)
```

---

## 🔧 Configuración Requerida

- `OPENAI_API_KEY`: Clave API de OpenAI (requerida)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: Opcionales, solo para Textract
- Vector store inicializado en `src/data/vectorstore/`

---

## 📝 Notas de Implementación

1. **Manejo de Errores**: Todos los agentes incluyen manejo de errores con fallbacks cuando es posible
2. **Idioma**: La mayoría de respuestas están en español según el README del proyecto
3. **LLMs**: Usa GPT-4o-mini para balance entre costo y calidad
4. **Vector Store**: Integración completa con Pinecone para búsqueda semántica usando embeddings de OpenAI text-embedding-3-small
5. **Extensibilidad**: Fácil agregar nuevas herramientas siguiendo el patrón existente

---

## 🎯 Próximos Pasos Sugeridos

1. Integrar APIs reales en `researcher_tool` (NASA, arXiv)
2. Implementar base de datos persistente para `memory_tool`
3. Agregar más validaciones científicas en `validator_tool`
4. Implementar caché para respuestas frecuentes
5. Agregar métricas y logging detallado

---

**Última actualización**: Todos los agentes están completos y funcionales ✅

