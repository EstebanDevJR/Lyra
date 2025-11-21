# Workflows de n8n para Lyra - Guía Completa

Esta guía te ayudará a configurar los 4 workflows principales para integrar datos astronómicos en tiempo real.

## 📋 Requisitos Previos

1. **n8n instalado** en Digital Ocean
2. **APIs configuradas**:
   - NASA API Key (https://api.nasa.gov)
   - OpenAI API Key (para resúmenes de papers)
3. **Variables de entorno** en el frontend (`Chatbot/.env.local`):
```env
NEXT_PUBLIC_N8N_NEWS_WEBHOOK=http://tu-droplet:5678/webhook/news
NEXT_PUBLIC_N8N_ASTRONOMY_IMAGE_WEBHOOK=http://tu-droplet:5678/webhook/astronomy-image
NEXT_PUBLIC_N8N_RESEARCH_PAPERS_WEBHOOK=http://tu-droplet:5678/webhook/research-papers
NEXT_PUBLIC_N8N_ASTRO_ALERTS_WEBHOOK=http://tu-droplet:5678/webhook/astro-alerts
NASA_API_KEY=tu_nasa_api_key_aqui
```

---

## 🖼️ Workflow 1: Imágenes Astronómicas del Día

### Objetivo
Obtener la imagen astronómica del día de NASA APOD y otras fuentes.

### Estructura del Workflow

```
[Schedule Trigger] → [HTTP Request: NASA APOD] → [Set Data] → [Respond to Webhook]
```

### Configuración Paso a Paso

#### 1. **Webhook Trigger** (Recomendado para on-demand)
- **Path**: `astronomy-image`
- **Method**: GET
- **Authentication**: None

> **Alternativa**: Si prefieres Schedule Trigger (ejecuta automáticamente cada día), sigue el apartado al final de esta sección.

#### 2. **HTTP Request: NASA APOD**
- **Method**: GET
- **URL**: `https://api.nasa.gov/planetary/apod`
- **Query Parameters**:
  - `api_key`: `{{$env.NASA_API_KEY}}` o tu API key
  - `hd`: `true`

#### 3. **Set Data (Format Response)**
```javascript
// Code Node o Set node
return {
  json: {
    title: $json.title,
    explanation: $json.explanation,
    url: $json.url,
    hdurl: $json.hdurl || $json.url,
    date: $json.date,
    copyright: $json.copyright || 'NASA',
    media_type: $json.media_type
  }
};
```

#### 4. **Respond to Webhook**
- **Response Mode**: When last node finishes
- **Response Data**: First Entry Only (ya que APOD devuelve un solo objeto)

### URL del Webhook
```
http://tu-droplet:5678/webhook/astronomy-image
```

---

### 📌 Variante con Schedule + Cache (Opcional)

Si quieres que el workflow se ejecute automáticamente cada día Y responda a webhooks, necesitas crear **dos workflows separados**:

**Workflow A: Fetch y Cache (Schedule)**
```
[Schedule: Daily 06:00] → [HTTP: NASA APOD] → [Store in Database/Variable]
```

**Workflow B: Serve Data (Webhook)**
```
[Webhook] → [Read from Database/Variable] → [Respond to Webhook]
```

Esto requiere configurar una base de datos externa (PostgreSQL, MongoDB) o usar las variables de entorno de n8n para cachear la respuesta.

---

## 📚 Workflow 2: Papers Científicos Recientes (ArXiv)

### Objetivo
Obtener papers recientes de ArXiv sobre astrofísica y generar resúmenes con IA.

### Estructura del Workflow

```
[Schedule] → [HTTP: ArXiv API] → [Loop] → [OpenAI Summary] → [Format] → [Webhook Response]
```

### Configuración Paso a Paso

#### 1. **Webhook Trigger**
- **Path**: `research-papers`
- **Method**: GET
- **Authentication**: None

> **Nota**: Este workflow es más pesado (llama a OpenAI para cada paper). Considera implementar caching si lo usas con Schedule.

#### 2. **HTTP Request: ArXiv**
- **Method**: GET
- **URL**: `http://export.arxiv.org/api/query`
- **Query Parameters**:
  - `search_query`: `cat:astro-ph.HE OR cat:astro-ph.CO OR cat:astro-ph.GA`
  - `sortBy`: `submittedDate`
  - `sortOrder`: `descending`
  - `max_results`: `10`

#### 3. **Code Node: Parse XML** (Solución sin dependencias externas)
```javascript
// ArXiv devuelve XML - Parsear sin xml2js usando regex y manipulación de strings
// IMPORTANTE: Asegurarse de que el HTTP Request tenga "Response Format: String" o "Auto"

// Obtener los datos XML de diferentes posibles ubicaciones
let rawData = $input.first().json.body || 
              $input.first().json.data || 
              $input.first().json || 
              $input.first().binary?.data?.toString() ||
              '';

// Convertir a string si no lo es
let xmlData = '';
if (typeof rawData === 'string') {
  xmlData = rawData;
} else if (typeof rawData === 'object') {
  // Si es un objeto, intentar convertirlo a string
  xmlData = JSON.stringify(rawData);
} else {
  xmlData = String(rawData);
}

// Si aún no tenemos datos, intentar desde el input completo
if (!xmlData || xmlData.length < 100) {
  const allData = $input.all();
  if (allData.length > 0) {
    const firstItem = allData[0];
    xmlData = firstItem.json?.body || 
              firstItem.json?.data || 
              firstItem.binary?.data?.toString() || 
              JSON.stringify(firstItem.json) || 
              '';
  }
}

// Verificar que tenemos XML válido
if (!xmlData || typeof xmlData !== 'string' || !xmlData.includes('<entry')) {
  throw new Error('No se pudo obtener el XML. Verifica que el HTTP Request devuelva el XML como string. Asegúrate de configurar "Response Format: String" en el nodo HTTP Request.');
}

// Función simple para extraer contenido de tags XML
function getXmlValue(xml, tagName) {
  const regex = new RegExp(`<${tagName}[^>]*>([\\s\\S]*?)<\\/${tagName}>`, 'g');
  const matches = [];
  let match;
  while ((match = regex.exec(xml)) !== null) {
    let content = match[1].trim();
    // Remover CDATA si existe
    content = content.replace(/<!\[CDATA\[(.*?)\]\]>/g, '$1');
    matches.push(content);
  }
  return matches;
}

function getXmlAttribute(xml, tagName, attribute) {
  const regex = new RegExp(`<${tagName}[^>]*${attribute}="([^"]+)"`, 'g');
  const match = regex.exec(xml);
  return match ? match[1] : null;
}

function cleanHtmlEntities(text) {
  if (!text) return '';
  return text
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&apos;/g, "'")
    .trim();
}

// Extraer todas las entradas (entries) - ahora xmlData es garantizado string
const entryMatches = xmlData.match(/<entry[^>]*>([\s\S]*?)<\/entry>/g) || [];

if (entryMatches.length === 0) {
  throw new Error('No se encontraron entradas en el XML. Verifica la respuesta del API de ArXiv.');
}

const entries = entryMatches.map((entryXml, index) => {
  try {
    // Extraer campos
    const id = getXmlValue(entryXml, 'id')[0] || '';
    const title = getXmlValue(entryXml, 'title')[0] || '';
    const summary = getXmlValue(entryXml, 'summary')[0] || '';
    const published = getXmlValue(entryXml, 'published')[0] || '';
    
    // Extraer autores (puede haber múltiples)
    const authorNames = getXmlValue(entryXml, 'name');
    const authors = authorNames.length > 0 ? authorNames.join(', ') : 'Unknown';
    
    // Extraer categoría
    const categoryTerm = getXmlAttribute(entryXml, 'category', 'term') || 'Astrophysics';
    
    // Limpiar HTML entities y espacios
    const cleanTitle = cleanHtmlEntities(title);
    const cleanAbstract = cleanHtmlEntities(summary);
    const paperId = id.split('/').pop() || id || `paper-${index}`;
    
    return {
      json: {
        id: paperId,
        title: cleanTitle,
        authors: authors,
        abstract: cleanAbstract,
        published: published,
        link: id,
        category: categoryTerm
      }
    };
  } catch (error) {
    console.error(`Error parsing entry ${index}:`, error);
    return null;
  }
}).filter(entry => entry !== null); // Filtrar entradas que fallaron

return entries;
```

**⚠️ IMPORTANTE - Configuración del nodo HTTP Request:**
- En el nodo HTTP Request, ve a **Options** → **Response Format**
- Selecciona **"String"** o **"Auto"** (no "JSON")
- Esto asegura que el XML llegue como string y no como objeto parseado

**Alternativa más robusta usando el parser XML nativo de Node.js** (si está disponible):
```javascript
// Alternativa: Usar el parser XML nativo (puede no estar disponible en todas las versiones de n8n)
const xmlData = $input.first().json.body || $input.first().json;

try {
  // Intentar usar DOMParser si está disponible (en algunos entornos de Node.js)
  const { DOMParser } = require('@xmldom/xmldom');
  const parser = new DOMParser();
  const xmlDoc = parser.parseFromString(xmlData, 'text/xml');
  
  const entries = Array.from(xmlDoc.getElementsByTagName('entry')).map(entry => {
    const id = entry.getElementsByTagName('id')[0]?.textContent || '';
    const title = entry.getElementsByTagName('title')[0]?.textContent || '';
    const summary = entry.getElementsByTagName('summary')[0]?.textContent || '';
    const published = entry.getElementsByTagName('published')[0]?.textContent || '';
    
    const authors = Array.from(entry.getElementsByTagName('author'))
      .map(author => author.getElementsByTagName('name')[0]?.textContent)
      .filter(Boolean)
      .join(', ');
    
    const category = entry.getElementsByTagName('category')[0]?.getAttribute('term') || 'Astrophysics';
    
    return {
      json: {
        id: id.split('/').pop() || id,
        title: title.trim(),
        authors: authors || 'Unknown',
        abstract: summary.trim(),
        published: published,
        link: id,
        category: category
      }
    };
  });
  
  return entries;
} catch (error) {
  // Fallback a solución con regex si DOMParser no está disponible
  // (usar el código de la primera solución arriba)
  throw new Error('XML parsing failed. Use the regex-based solution instead.');
}
```

> **Recomendación**: Usa la primera solución (regex) ya que no requiere dependencias externas y funciona en todos los entornos de n8n.

#### 4. **Loop Over Items**
- Itera sobre cada paper

#### 5. **OpenAI Node: Generate Summary**
- **Operation**: Message a Model
- **Model**: gpt-4o-mini
- **Prompt**:
```
Summarize this astrophysics paper in 2-3 sentences for a general audience:

Title: {{$json.title}}
Abstract: {{$json.abstract}}

Summary:
```

#### 6. **Set Node: Combine Data**
```javascript
// IMPORTANTE: Este nodo debe estar DESPUÉS del nodo OpenAI dentro del loop
// La estructura del workflow debe ser: Parse XML → Loop → [Paper Data] → OpenAI → Set Node
// ⚠️ REEMPLAZA 'Parse XML' con el nombre REAL de tu nodo que parsea el XML

// Obtener el resumen de OpenAI (viene del nodo anterior directamente conectado)
let summary = '';
if ($json.message && $json.message.content) {
  summary = $json.message.content;
} else if ($json.content) {
  summary = $json.content;
}

// Obtener los datos originales del paper desde el nodo anterior en el loop
// En n8n, dentro de un loop, debes referenciar el nodo anterior por su nombre
let paperData = {};

// Opción 1: Acceder al nodo que parsea el XML (REEMPLAZA 'Parse XML' con el nombre real)
try {
  // ⚠️ CAMBIA 'Parse XML' por el nombre exacto de tu nodo que parsea el XML
  const parseNode = $('Parse XML'); // <-- CAMBIA ESTE NOMBRE
  if (parseNode && parseNode.item && parseNode.item.json) {
    paperData = parseNode.item.json;
  }
} catch (e) {
  console.log('Could not access Parse XML node, trying alternatives...');
}

// Opción 2: Si los datos están en $input.item (cuando el loop preserva el contexto)
if ((!paperData.id && !paperData.title) && $input && $input.item && $input.item.json) {
  const itemData = $input.item.json;
  if (itemData.id || itemData.title) {
    paperData = itemData;
  }
}

// Opción 3: Si el nodo anterior al OpenAI tiene los datos del paper
// Intenta acceder al nodo que está antes de OpenAI en el loop
// (Reemplaza 'NombreDelNodoAnterior' con el nombre real)
try {
  // Si tienes un nodo entre Parse XML y OpenAI, úsalo aquí
  // const previousNode = $('NombreDelNodoAnterior');
  // if (previousNode && previousNode.item && previousNode.item.json) {
  //   const prevData = previousNode.item.json;
  //   if (prevData.id || prevData.title) {
  //     paperData = prevData;
  //   }
  // }
} catch (e) {
  // Ignorar si no existe
}

// Combinar todo
return {
  json: {
    id: paperData.id || '',
    title: paperData.title || '',
    authors: paperData.authors || 'Unknown',
    abstract: paperData.abstract || '',
    summary: summary || (paperData.abstract ? paperData.abstract.substring(0, 200) + '...' : ''),
    published: paperData.published || '',
    link: paperData.link || '',
    category: paperData.category || 'Astrophysics'
  }
};
```

**🔧 Solución alternativa más simple (si el loop no preserva los datos):**

Si la solución anterior no funciona, usa un nodo **"Set"** (no Code) para combinar los datos:

1. **Nodo Set (Mode: Manual)**
   - Agrega campos:
     - `id`: `{{ $('Parse XML').item.json.id }}`
     - `title`: `{{ $('Parse XML').item.json.title }}`
     - `authors`: `{{ $('Parse XML').item.json.authors }}`
     - `abstract`: `{{ $('Parse XML').item.json.abstract }}`
     - `summary`: `{{ $json.message.content }}` (del nodo OpenAI)
     - `published`: `{{ $('Parse XML').item.json.published }}`
     - `link`: `{{ $('Parse XML').item.json.link }}`
     - `category`: `{{ $('Parse XML').item.json.category }}`

2. Reemplaza `'Parse XML'` con el nombre real de tu nodo que parsea el XML.

**⚠️ Nota importante sobre la estructura del workflow:**
- Si el nodo OpenAI está **dentro del loop** y directamente conectado antes de este nodo Set, usa: `$json.message.content`
- Si el nodo OpenAI está **fuera del loop**, necesitas usar `$('NombreDelNodoOpenAI').item.json.message.content` (reemplaza 'NombreDelNodoOpenAI' con el nombre real de tu nodo)
- El código arriba intenta todas las opciones automáticamente

#### 7. **Aggregate (All Items)**
- Combina todos los resultados en un array
- **Mode**: Aggregate All Items
- **Aggregate**: All Items
- Esto combina todos los papers procesados en un solo array

#### 8. **Respond to Webhook**
- **Response Mode**: When last node finishes
- **Response Data**: All Entries

**⚠️ IMPORTANTE - Configuración del Aggregate:**
- El nodo Aggregate debe estar configurado en modo **"Aggregate All Items"**
- Esto asegura que todos los papers se combinen en un solo array
- Conecta el Aggregate **directamente** al "Respond to Webhook" (sin nodos intermedios)

**Si el webhook devuelve formato incorrecto** (ej: `[{ data: [...] }]` en lugar de `[{...}, {...}]`):

**Opción 1: Usar nodo Set (Recomendado)**
- Agrega un nodo **Set** entre Aggregate y Webhook
- **Mode**: Keep Only Set Fields
- **Fields to Set**: Deja vacío (esto pasa los datos tal cual pero en formato correcto)
- O configura campos individuales si necesitas transformar

**Opción 2: Configurar el Aggregate correctamente**
- En el nodo Aggregate, asegúrate de que **"Put Output in Field"** esté vacío o configurado como `json`
- Esto asegura que cada item mantenga su estructura `{ json: {...} }` que el webhook puede procesar correctamente

**Nota**: La ruta API del frontend ya maneja múltiples formatos, así que debería funcionar incluso si n8n devuelve `[{ data: [...] }]`.

### URL del Webhook
```
http://tu-droplet:5678/webhook/research-papers
```

> ⚠️ **Advertencia de Costos**: Este workflow llama a OpenAI API por cada paper (10 papers = 10 llamadas). Considera implementar caching o limitar los resultados.

---

## ⚠️ Workflow 3: Alertas Astronómicas (NASA NEO)

### Objetivo
Monitorear objetos cercanos a la Tierra y eventos solares.

### Estructura del Workflow

```
[Schedule] → [HTTP: NASA NEO] → [Filter] → [HTTP: Solar Events] → [Merge] → [Format] → [Webhook]
```

### Configuración Paso a Paso

#### 1. **Webhook Trigger**
- **Path**: `astro-alerts`
- **Method**: GET
- **Authentication**: None

> **Recomendación**: Para alertas críticas en tiempo real, considera usar Schedule (cada hora) + notificaciones push en lugar de webhook on-demand.

#### 2. **HTTP Request: NASA NEO**
- **Method**: GET
- **URL**: `https://api.nasa.gov/neo/rest/v1/feed`
- **Query Parameters**:
  - `api_key`: `{{$env.NASA_API_KEY}}`
  - `start_date`: `{{$now.format('YYYY-MM-DD')}}`
  - `end_date`: `{{$now.plus(7, 'days').format('YYYY-MM-DD')}}`

#### 3. **Code Node: Parse NEO Data**
```javascript
const neos = $json.near_earth_objects;
const alerts = [];

for (const date in neos) {
  for (const neo of neos[date]) {
    const closeApproach = neo.close_approach_data[0];
    const distance = parseFloat(closeApproach.miss_distance.kilometers);
    const isPotentiallyHazardous = neo.is_potentially_hazardous_asteroid;
    
    // Solo alertar si está relativamente cerca o es peligroso
    if (distance < 10000000 || isPotentiallyHazardous) {
      alerts.push({
        id: neo.id,
        title: `Near Earth Object: ${neo.name}`,
        description: `Asteroid will pass within ${(distance / 1000000).toFixed(2)} million km on ${closeApproach.close_approach_date_full}. Diameter: ${neo.estimated_diameter.meters.estimated_diameter_max.toFixed(0)}m`,
        type: 'neo',
        severity: isPotentiallyHazardous ? 'warning' : 'info',
        date: closeApproach.close_approach_date,
        link: neo.nasa_jpl_url
      });
    }
  }
}

return alerts.map(alert => ({ json: alert }));
```

#### 4. **HTTP Request: Solar Activity (Opcional)**
- **URL**: `https://services.swpc.noaa.gov/json/goes/primary/xrays-7-day.json`

#### 5. **Aggregate + Format**
- Combina NEO y eventos solares

#### 6. **Respond to Webhook**
- **Response Mode**: When last node finishes
- **Response Data**: All Entries

### URL del Webhook
```
http://tu-droplet:5678/webhook/astro-alerts
```

### 🔔 Variante con Notificaciones (Avanzado)

Para recibir alertas **proactivamente** en lugar de consultarlas:
```
[Schedule: Every hour] → [HTTP: NASA NEO] → [Filter: Critical Only] → [Send Email/Discord/Telegram]
```

---

## 📰 Workflow 4: Noticias (Ya Implementado)

Ya tienes este configurado. Solo asegúrate de:
- **Respond With**: All Items (no First Item)
- **Response Data**: Use el array completo `items`

---

## 🔧 Variables de Entorno en n8n

En tu n8n en Digital Ocean, configura estas variables:

```env
NASA_API_KEY=tu_nasa_api_key
OPENAI_API_KEY=tu_openai_api_key
```

Accede a: Settings → Variables de Entorno

---

## 🚀 Activar los Workflows

1. **Guarda** cada workflow
2. **Activa** el workflow (switch en la esquina superior derecha)
3. **Prueba** con "Execute Workflow" para verificar que funciona
4. **Copia la URL de producción** (no la de -test)

---

## 🧪 Probar las Integraciones

### Desde tu navegador:
```bash
# Test Astronomy Image
curl http://tu-droplet:5678/webhook/astronomy-image

# Test Research Papers
curl http://tu-droplet:5678/webhook/research-papers

# Test Astro Alerts
curl http://tu-droplet:5678/webhook/astro-alerts
```

### Desde el frontend:
1. Recarga la página principal de Lyra
2. Desplázate hacia abajo después de la sección de información del proyecto
3. Deberías ver la nueva sección "Latest in Astronomy"

---

## 📊 Estructura de Datos Esperada

### Astronomy Image
```json
{
  "title": "...",
  "explanation": "...",
  "url": "...",
  "hdurl": "...",
  "date": "2025-11-21",
  "copyright": "...",
  "media_type": "image"
}
```

### Research Papers
```json
[
  {
    "id": "2511.xxxxx",
    "title": "...",
    "authors": "...",
    "abstract": "...",
    "summary": "AI-generated summary...",
    "published": "2025-11-20",
    "link": "https://arxiv.org/abs/...",
    "category": "Black Holes"
  }
]
```

### Astro Alerts
```json
[
  {
    "id": "...",
    "title": "...",
    "description": "...",
    "type": "neo|solar|meteor|eclipse|comet",
    "severity": "info|warning|critical",
    "date": "2025-11-25",
    "link": "..."
  }
]
```

---

## 🐛 Troubleshooting

### Los datos no llegan al frontend
1. Verifica que los workflows estén **activos**
2. Verifica las URLs en `.env.local`
3. Revisa los logs del servidor Next.js (`npm run dev`)
4. Prueba los webhooks directamente con `curl`

### Error "N8N_URL not configured"
- Asegúrate de tener las variables en `.env.local`
- Reinicia el servidor de Next.js después de cambiar `.env`

### Solo llega 1 item en lugar de un array
- En n8n, verifica que "Respond With" esté en **"All Items"**
- Revisa el nodo "Aggregate" si estás combinando múltiples requests

---

## 🎯 Próximos Pasos

Una vez que estos 4 workflows funcionen, considera añadir:
- **Caching** en las API routes (Next.js revalidation)
- **Base de datos** (Supabase) para histórico
- **Notificaciones push** para alertas críticas
- **Panel de administración** para configurar qué fuentes mostrar

---

## 🔄 Caching con Supabase (Arquitectura Avanzada)

Si quieres combinar **Schedule automático** + **respuesta rápida a webhooks**, usa esta arquitectura:

### Setup en Supabase

```sql
-- Tabla para cachear datos astronómicos
CREATE TABLE astronomical_data (
  id SERIAL PRIMARY KEY,
  data_type VARCHAR(50) NOT NULL, -- 'apod', 'papers', 'alerts', 'news'
  data JSONB NOT NULL,
  fetched_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP
);

CREATE INDEX idx_data_type ON astronomical_data(data_type);
CREATE INDEX idx_expires_at ON astronomical_data(expires_at);
```

### Workflow A: Fetch + Cache (Schedule)

```
[Schedule: Daily] 
  → [HTTP: NASA/ArXiv/etc] 
  → [Supabase: INSERT/UPDATE] 
    (guarda en astronomical_data con data_type='apod')
```

**Nodo Supabase**:
```sql
INSERT INTO astronomical_data (data_type, data, expires_at)
VALUES (
  'apod',
  '{{$json}}'::jsonb,
  NOW() + INTERVAL '1 day'
)
ON CONFLICT (data_type) 
DO UPDATE SET 
  data = EXCLUDED.data,
  fetched_at = NOW(),
  expires_at = EXCLUDED.expires_at;
```

### Workflow B: Serve Cache (Webhook)

```
[Webhook Trigger]
  → [Supabase: SELECT]
  → [IF: Check if expired]
    → Yes: [HTTP: Fetch Fresh] → [Update Cache] → [Respond]
    → No: [Respond with Cache]
```

**Nodo Supabase**:
```sql
SELECT data, fetched_at, expires_at
FROM astronomical_data
WHERE data_type = 'apod'
  AND expires_at > NOW()
ORDER BY fetched_at DESC
LIMIT 1;
```

### Beneficios
- ✅ Datos siempre actualizados automáticamente
- ✅ Respuesta instantánea a webhooks (desde cache)
- ✅ Reducción de llamadas a APIs externas
- ✅ Histórico de datos para análisis

---

## 💡 Simplificación para Empezar

Si quieres empezar simple, usa **solo Webhooks** (on-demand):
- El frontend solicita datos cuando el usuario carga la página
- Sin caching, sin complejidad extra
- Funciona perfectamente para < 1000 usuarios/día

Después, cuando escales, implementa caching con Supabase.

---

**¿Necesitas ayuda configurando alguno de estos workflows?** Avísame y te guío paso a paso en n8n.

