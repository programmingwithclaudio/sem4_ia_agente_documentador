"""
Sistema de Documentación con IA V4 - AGENTE CONVERSACIONAL
✅ Saludo natural y contexto del proyecto
✅ Personalidad conversacional como experto
✅ Generación de README.md profesional
✅ Selector de carpeta para documentación
✅ Interacción fluida e inteligente
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv

import gradio as gr
import numpy as np
import faiss
import redis
import pandas as pd
from sentence_transformers import SentenceTransformer

from openai import OpenAI
import anthropic

load_dotenv()

MODEL_CONFIG = {
    "GPT": {
        "model": "gpt-4o",
        "api_key": os.getenv('OPENAI_API_KEY', ''),
        "max_tokens": 4000
    },
    "Claude": {
        "model": "claude-3-5-sonnet-20241022",
        "api_key": os.getenv('ANTHROPIC_API_KEY', ''),
        "max_tokens": 4000
    },
    "DeepSeek": {
        "model": "deepseek-chat",
        "api_key": os.getenv('DEEPSEEK_API_KEY', ''),
        "base_url": "https://api.deepseek.com",
        "max_tokens": 4000
    }
}

EMBEDDINGS_PATH = Path("datasets/embeddings")
DOCS_OUTPUT_PATH = Path("documentacion_generada")
DOCS_OUTPUT_PATH.mkdir(exist_ok=True)


class DocumentationSystemV4:
    """
    Sistema conversacional que actúa como un experto del proyecto
    """
    
    def __init__(self):
        self.clients = {}
        self.embedding_model = None
        self.faiss_index = None
        self.redis_client = None
        self.mapeo_indices = None
        self.conversation_history = []
        
        self.embedding_dim = 384
        self.num_features = 8
        self.total_dim = 392
        
        self.cache_endpoints = None
        self.cache_archivos = None
        self.cache_routers = None
        
        # ✅ NUEVO: Estado conversacional
        self.proyecto_nombre = "API Backend"
        self.saludo_inicial_enviado = False
        self.contexto_mostrado = False
        
        self._initialize_clients()
        self._load_embeddings_v3()
        self._cargar_cache_completo()
        self._analizar_proyecto()  # ✅ NUEVO
    
    def _initialize_clients(self):
        """Inicializa clientes LLM"""
        if MODEL_CONFIG["GPT"]["api_key"]:
            try:
                self.clients["GPT"] = OpenAI(api_key=MODEL_CONFIG["GPT"]["api_key"])
                print("✅ GPT-4o disponible")
            except Exception as e:
                print(f"⚠️ Error GPT: {e}")
        
        if MODEL_CONFIG["Claude"]["api_key"]:
            try:
                self.clients["Claude"] = anthropic.Anthropic(
                    api_key=MODEL_CONFIG["Claude"]["api_key"]
                )
                print("✅ Claude disponible")
            except Exception as e:
                print(f"⚠️ Error Claude: {e}")
        
        if MODEL_CONFIG["DeepSeek"]["api_key"]:
            try:
                self.clients["DeepSeek"] = OpenAI(
                    api_key=MODEL_CONFIG["DeepSeek"]["api_key"],
                    base_url=MODEL_CONFIG["DeepSeek"]["base_url"]
                )
                print("✅ DeepSeek disponible")
            except Exception as e:
                print(f"⚠️ Error DeepSeek: {e}")
    
    def _load_embeddings_v3(self):
        """Carga embeddings"""
        try:
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            self.embedding_model.max_seq_length = 512
            print("✅ Modelo cargado")
            
            index_path = EMBEDDINGS_PATH / "documentacion.index"
            if index_path.exists():
                self.faiss_index = faiss.read_index(str(index_path))
                self.total_dim = self.faiss_index.d
                self.num_features = self.total_dim - self.embedding_dim
                print(f"✅ FAISS: {self.faiss_index.ntotal} vectores")
            
            self.redis_client = redis.Redis(
                host='localhost', port=6379, db=3, decode_responses=True
            )
            self.redis_client.ping()
            print("✅ Redis DB3")
            
            mapeo_path = EMBEDDINGS_PATH / "mapeo_indices.json"
            if mapeo_path.exists():
                with open(mapeo_path, 'r', encoding='utf-8') as f:
                    self.mapeo_indices = json.load(f)
                print(f"✅ Mapeo: {len(self.mapeo_indices)} entradas")
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
    
    def _cargar_cache_completo(self):
        """Carga todos los datos en memoria"""
        if not self.redis_client or not self.mapeo_indices:
            return
        
        try:
            print("\n📦 Cargando cache...")
            
            self.cache_endpoints = []
            self.cache_archivos = {}
            self.cache_routers = {}
            
            for idx in range(len(self.mapeo_indices)):
                data = self.redis_client.hgetall(f"chunk:{idx}")
                if data:
                    tipo = data.get('tipo', '')
                    
                    if tipo == 'route' or data.get('endpoint') or data.get('endpoint_completo'):
                        endpoint_completo = data.get('endpoint_completo', '')
                        endpoint_base = data.get('endpoint', '')
                        router_prefix = data.get('router_prefix', '')
                        
                        if endpoint_completo:
                            endpoint_final = endpoint_completo
                        elif endpoint_base and router_prefix:
                            endpoint_final = f"{router_prefix}{endpoint_base}".replace('//', '/')
                        else:
                            endpoint_final = endpoint_base
                        
                        if endpoint_final:
                            endpoint_info = {
                                'id': idx,
                                'endpoint': endpoint_final,
                                'metodo': data.get('metodo_http', 'HTTP'),
                                'descripcion': data.get('descripcion', ''),
                                'archivo': data.get('archivo', ''),
                                'elemento': data.get('elemento', ''),
                                'router_padre': data.get('router_padre', ''),
                                'response_model': data.get('response_model', ''),
                                'status_code': data.get('status_code', ''),
                                'codigo': data.get('contenido', '')[:500]
                            }
                            self.cache_endpoints.append(endpoint_info)
                    
                    archivo = data.get('archivo', '')
                    if archivo:
                        if archivo not in self.cache_archivos:
                            self.cache_archivos[archivo] = []
                        self.cache_archivos[archivo].append({
                            'id': idx,
                            'tipo': tipo,
                            'elemento': data.get('elemento', ''),
                            'descripcion': data.get('descripcion', '')[:200]
                        })
                    
                    router_padre = data.get('router_padre', '')
                    if router_padre:
                        if router_padre not in self.cache_routers:
                            self.cache_routers[router_padre] = []
                        self.cache_routers[router_padre].append({
                            'id': idx,
                            'tipo': tipo,
                            'elemento': data.get('elemento', ''),
                            'endpoint': endpoint_final if endpoint_final else ''
                        })
            
            print(f"✅ Cache: {len(self.cache_endpoints)} endpoints, {len(self.cache_archivos)} archivos")
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
    
    def _analizar_proyecto(self):
        """
        ✅ NUEVO: Analiza el proyecto para entender su propósito
        """
        if not self.cache_archivos:
            return
        
        # Detectar tipo de proyecto por archivos
        archivos = list(self.cache_archivos.keys())
        
        if any('auth' in a.lower() for a in archivos):
            self.proyecto_nombre = "API Backend con Autenticación"
        elif any('user' in a.lower() for a in archivos):
            self.proyecto_nombre = "API de Gestión de Usuarios"
        elif any('product' in a.lower() for a in archivos):
            self.proyecto_nombre = "API de E-commerce"
        else:
            self.proyecto_nombre = "API Backend FastAPI"
    
    def generar_saludo_inicial(self) -> str:
        """
        ✅ NUEVO: Saludo natural y contextual
        """
        if not self.cache_endpoints:
            return """
¡Hola! 👋 

Soy tu asistente de documentación de código. Estoy aquí para ayudarte a entender y documentar tu proyecto.

Parece que aún no he cargado datos del proyecto. ¿Podrías verificar que los archivos de embeddings estén correctamente generados?
"""
        
        num_endpoints = len(self.cache_endpoints)
        num_archivos = len(self.cache_archivos)
        routers_principales = sorted(self.cache_routers.keys())[:5]
        
        saludo = f"""
¡Hola! 👋 Soy tu asistente de documentación para **{self.proyecto_nombre}**.

He analizado tu código y tengo todo listo. Aquí un resumen de lo que conozco:

📊 **Proyecto en números:**
- 🌐 **{num_endpoints} endpoints** documentados
- 📁 **{num_archivos} archivos** analizados
- 📦 **{len(self.cache_routers)} routers** organizados

🔍 **Principales módulos:**
{chr(10).join([f"   • {router}" for router in routers_principales])}

---

💬 **¿En qué puedo ayudarte?**

Puedo responder preguntas como:
- *"¿Qué endpoints tiene la API?"*
- *"¿Cómo funciona el sistema de autenticación?"*
- *"Explícame el endpoint /users"*
- *"Genera un README.md completo"*

También puedo generar documentación profesional si lo necesitas. ¡Pregunta lo que quieras! 🚀
"""
        
        return saludo
    
    def detectar_tipo_pregunta(self, pregunta: str) -> str:
        """Detecta el tipo de pregunta"""
        pregunta_lower = pregunta.lower()
        
        # Preguntas de saludo/presentación
        if any(kw in pregunta_lower for kw in ['hola', 'hey', 'buenos días', 'buenas tardes', 'qué tal']):
            return 'SALUDO'
        
        # Preguntas sobre generación de documentación
        if any(kw in pregunta_lower for kw in ['readme', 'documentación', 'documenta', 'genera doc']):
            return 'GENERAR_DOC'
        
        # Preguntas que requieren listas completas
        keywords_lista = [
            'endpoints', 'rutas', 'api', 'listar', 'mostrar todos',
            'cuántos', 'qué endpoints', 'qué rutas', 'lista de',
            'archivos', 'módulos', 'estructura', 'routers'
        ]
        
        if any(kw in pregunta_lower for kw in keywords_lista):
            return 'LISTA'
        
        # Preguntas sobre código específico
        keywords_codigo = [
            'cómo funciona', 'implementa', 'código de', 'función',
            'clase', 'método', 'explica', 'muestra el código'
        ]
        
        if any(kw in pregunta_lower for kw in keywords_codigo):
            return 'CODIGO'
        
        return 'GENERAL'
    
    def obtener_todos_endpoints(self) -> List[Dict]:
        """Obtiene todos los endpoints del cache"""
        return self.cache_endpoints if self.cache_endpoints else []
    
    def buscar_codigo_semantico(self, query: str, top_k: int = 5) -> List[Dict]:
        """Búsqueda semántica"""
        if not self.faiss_index or not self.embedding_model:
            return []
        
        try:
            query_embedding = self.embedding_model.encode(
                [query], convert_to_numpy=True, normalize_embeddings=True
            )
            
            features_dummy = np.zeros((1, self.num_features), dtype='float32')
            query_embedding = np.hstack([query_embedding, features_dummy]).astype('float32')
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            
            distances, indices = self.faiss_index.search(query_embedding, top_k)
            
            resultados = []
            for idx, dist in zip(indices[0], distances[0]):
                chunk_data = self.redis_client.hgetall(f"chunk:{idx}")
                if chunk_data:
                    endpoint_completo = chunk_data.get('endpoint_completo', '')
                    endpoint_base = chunk_data.get('endpoint', '')
                    router_prefix = chunk_data.get('router_prefix', '')
                    
                    if endpoint_completo:
                        endpoint_final = endpoint_completo
                    elif endpoint_base and router_prefix:
                        endpoint_final = f"{router_prefix}{endpoint_base}".replace('//', '/')
                    else:
                        endpoint_final = endpoint_base
                    
                    resultado = {
                        'id': int(idx),
                        'score': float(dist),
                        'archivo': chunk_data.get('archivo', ''),
                        'tipo': chunk_data.get('tipo', ''),
                        'elemento': chunk_data.get('elemento', ''),
                        'endpoint': endpoint_final,
                        'metodo_http': chunk_data.get('metodo_http', ''),
                        'contenido': chunk_data.get('contenido', ''),
                        'descripcion': chunk_data.get('descripcion', ''),
                        'router_padre': chunk_data.get('router_padre', '')
                    }
                    
                    resultados.append(resultado)
            
            return resultados
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
    
    def generar_contexto_tecnico(self) -> str:
        """Genera contexto técnico del proyecto"""
        if not self.cache_endpoints:
            return "No hay datos disponibles"
        
        try:
            routers_map = {}
            for ep in self.cache_endpoints:
                router = ep.get('router_padre', 'main')
                if router not in routers_map:
                    routers_map[router] = []
                routers_map[router].append(ep)
            
            contexto = f"""
📊 **DATOS DEL PROYECTO:**
   • Total de endpoints: {len(self.cache_endpoints)}
   • Total de archivos: {len(self.cache_archivos)}
   • Total de routers: {len(self.cache_routers)}

🌐 **ENDPOINTS DE LA API:**

"""
            
            for router, endpoints in sorted(routers_map.items()):
                contexto += f"📦 **{router}**\n"
                for ep in sorted(endpoints, key=lambda x: x['endpoint'])[:20]:
                    contexto += f"   • {ep['metodo']:7} {ep['endpoint']}\n"
                contexto += "\n"
            
            return contexto
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def generar_readme_completo(self, carpeta_destino: str) -> Tuple[str, str]:
        """
        ✅ NUEVO: Genera README.md profesional
        """
        if not self.cache_endpoints:
            return "❌ No hay datos para generar README", ""
        
        try:
            # Agrupar endpoints
            routers_map = {}
            for ep in self.cache_endpoints:
                router = ep.get('router_padre', 'General')
                if router not in routers_map:
                    routers_map[router] = []
                routers_map[router].append(ep)
            
            # Generar contenido README
            readme = f"""# 📚 Documentación - {self.proyecto_nombre}

## 📋 Descripción del Proyecto

Este proyecto es una API REST desarrollada con FastAPI que proporciona {len(self.cache_endpoints)} endpoints organizados en {len(self.cache_routers)} routers principales.

## 🚀 Características

- ✅ API RESTful con FastAPI
- 🔐 Sistema de autenticación y autorización
- 📊 {len(self.cache_endpoints)} endpoints documentados
- 🗂️ Organizado en {len(self.cache_routers)} módulos

## 📁 Estructura del Proyecto

```
proyecto/
{chr(10).join([f"├── {archivo}" for archivo in sorted(list(self.cache_archivos.keys())[:15])])}
```

## 🌐 Endpoints de la API

### Resumen por Router

"""
            
            for router, endpoints in sorted(routers_map.items()):
                readme += f"\n#### 📦 {router}\n\n"
                readme += f"Total de endpoints: **{len(endpoints)}**\n\n"
                readme += "| Método | Endpoint | Descripción |\n"
                readme += "|--------|----------|-------------|\n"
                
                for ep in sorted(endpoints, key=lambda x: x['endpoint']):
                    metodo = ep['metodo']
                    endpoint = ep['endpoint']
                    desc = ep.get('descripcion', 'Sin descripción')[:50]
                    readme += f"| `{metodo}` | `{endpoint}` | {desc} |\n"
                
                readme += "\n"
            
            readme += f"""
## 🛠️ Instalación y Configuración

```bash
# Clonar repositorio
git clone <url-repositorio>

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Ejecutar servidor
uvicorn main:app --reload
```

## 📖 Uso de la API

### Autenticación

La API utiliza autenticación basada en tokens JWT. Para obtener un token:

```bash
curl -X POST "http://localhost:8000/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{{"username": "user", "password": "pass"}}'
```

### Ejemplo de Petición

```python
import requests

response = requests.get(
    "http://localhost:8000/api/endpoint",
    headers={{"Authorization": "Bearer <token>"}}
)
print(response.json())
```

## 📊 Estadísticas del Proyecto

- **Total de endpoints:** {len(self.cache_endpoints)}
- **Archivos analizados:** {len(self.cache_archivos)}
- **Routers organizados:** {len(self.cache_routers)}

## 📝 Notas

Esta documentación fue generada automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} usando el sistema de documentación con IA.

## 📄 Licencia

[Especificar licencia]

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request.
"""
            
            # Guardar archivo
            carpeta_path = Path(carpeta_destino) if carpeta_destino else DOCS_OUTPUT_PATH
            carpeta_path.mkdir(parents=True, exist_ok=True)
            
            readme_path = carpeta_path / "README.md"
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme)
            
            mensaje = f"""
✅ **README.md generado exitosamente**

📁 **Ubicación:** `{readme_path}`

📊 **Contenido incluido:**
- Descripción del proyecto
- {len(self.cache_endpoints)} endpoints documentados
- {len(self.cache_routers)} routers organizados
- Instrucciones de instalación y uso
- Ejemplos de código

🎉 ¡Tu documentación está lista! Puedes abrirla y personalizarla según necesites.
"""
            
            return mensaje, str(readme_path)
            
        except Exception as e:
            return f"❌ Error generando README: {str(e)}", ""


def crear_prompt_conversacional_v4(
    pregunta: str,
    tipo_pregunta: str,
    codigo: Optional[List[Dict]],
    endpoints: Optional[List[Dict]],
    contexto_tecnico: str,
    historial: List[Dict],
    proyecto_nombre: str
) -> str:
    """
    ✅ NUEVO: Prompt conversacional y natural
    """
    
    # Historial
    historial_texto = ""
    if historial:
        historial_texto = "\n**📜 CONTEXTO DE LA CONVERSACIÓN:**\n"
        for h in historial[-3:]:
            historial_texto += f"👤: {h['pregunta'][:80]}...\n"
            historial_texto += f"🤖: {h['respuesta'][:120]}...\n\n"
    
    # CASO: Pregunta de lista
    if tipo_pregunta == 'LISTA' and endpoints:
        endpoints_texto = "\n".join([
            f"   • {ep['metodo']:7} {ep['endpoint']:40} → {ep.get('descripcion', '')[:50]}"
            for ep in endpoints
        ])
        
        return f"""Eres un ingeniero senior experto en el proyecto "{proyecto_nombre}". 
Respondes de forma conversacional, profesional y amigable.

{contexto_tecnico}

═══════════════════════════════════════════════════════════════
ENDPOINTS DISPONIBLES
═══════════════════════════════════════════════════════════════

{endpoints_texto}

Total: {len(endpoints)} endpoints

{historial_texto}

═══════════════════════════════════════════════════════════════
👤 PREGUNTA:
═══════════════════════════════════════════════════════════════
{pregunta}

═══════════════════════════════════════════════════════════════
🎯 INSTRUCCIONES:
═══════════════════════════════════════════════════════════════
1. Responde de forma CONVERSACIONAL, como si fueras un compañero de equipo
2. Agrupa los endpoints por funcionalidad o router
3. Explica brevemente qué hace cada grupo
4. Menciona los más importantes o interesantes
5. Usa emojis y formato claro
6. NO seas robótico ni lista todos sin contexto

🤖 TU RESPUESTA:"""
    
    # CASO: Pregunta de código
    elif tipo_pregunta == 'CODIGO' and codigo:
        codigo_texto = ""
        for i, c in enumerate(codigo[:3], 1):
            codigo_texto += f"""
---
**Fragmento #{i}** (Relevancia: {c['score']:.1%})
📄 Archivo: `{c['archivo']}`
📌 Elemento: `{c['elemento']}`
{f"🌐 Endpoint: `{c['metodo_http']} {c['endpoint']}`" if c['endpoint'] else ""}

```python
{c['contenido'][:500]}
```
"""
        
        return f"""Eres un ingeniero senior experto en el proyecto "{proyecto_nombre}".
Respondes de forma conversacional, clara y pedagógica.

{contexto_tecnico}

═══════════════════════════════════════════════════════════════
CÓDIGO RELEVANTE
═══════════════════════════════════════════════════════════════
{codigo_texto}

{historial_texto}

═══════════════════════════════════════════════════════════════
👤 PREGUNTA:
═══════════════════════════════════════════════════════════════
{pregunta}

═══════════════════════════════════════════════════════════════
🎯 INSTRUCCIONES:
═══════════════════════════════════════════════════════════════
1. Responde como si explicaras a un colega
2. Usa el CÓDIGO que ves arriba para responder
3. Explica el "por qué" y el "cómo"
4. Menciona archivos y funciones específicas
5. Sé claro pero conversacional
6. Si no hay código relevante, di que necesitas más contexto

🤖 TU RESPUESTA:"""
    
    # CASO: Pregunta general
    else:
        return f"""Eres un ingeniero senior experto en el proyecto "{proyecto_nombre}".
Respondes de forma conversacional, profesional y útil.

{contexto_tecnico}

{historial_texto}

═══════════════════════════════════════════════════════════════
👤 PREGUNTA:
═══════════════════════════════════════════════════════════════
{pregunta}

═══════════════════════════════════════════════════════════════
🎯 INSTRUCCIONES:
═══════════════════════════════════════════════════════════════
1. Responde basándote en lo que conoces del proyecto
2. Sé conversacional y natural
3. Ofrece ejemplos concretos cuando sea posible
4. Si necesitas más información, pídela claramente
5. Mantén un tono profesional pero amigable

🤖 TU RESPUESTA:"""


def crear_interfaz():
    """Interfaz Gradio V4"""
    
    system = DocumentationSystemV4()
    modelos = list(system.clients.keys()) or ["GPT", "Claude", "DeepSeek"]
    
    css = """
    .main-title {
        text-align: center; 
        padding: 25px; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
        border-radius: 12px; 
        color: white;
        font-size: 28px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .chat-container {
        border: 2px solid #3498db; 
        border-radius: 12px; 
        padding: 15px;
        background: #f8f9fa;
    }
    .info-box {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        padding: 20px; 
        border-radius: 10px; 
        margin: 15px 0;
        border-left: 5px solid #667eea;
    }
    .success-box {
        background: #d4edda;
        border-left: 5px solid #28a745;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    """
    
    with gr.Blocks(css=css, title="Agente Conversacional V4") as interface:
        gr.Markdown("""
        # 🤖 Asistente Inteligente de Documentación
        ### Tu experto conversacional en arquitectura de código
        """, elem_classes=["main-title"])
        
        with gr.Row():
            # CHAT PRINCIPAL
            with gr.Column(scale=2):
                gr.Markdown("### 💬 Chat Conversacional")
                
                modelo_ia = gr.Dropdown(
                    choices=modelos,
                    label="🤖 Modelo de IA",
                    value=modelos[0] if modelos else "GPT",
                    interactive=True
                )
                
                chatbot = gr.Chatbot(
                    label="Conversación",
                    height=550,
                    elem_classes=["chat-container"],
                    show_copy_button=True
                )
                
                with gr.Row():
                    mensaje_input = gr.Textbox(
                        placeholder="💬 Escribe tu pregunta aquí... (Ej: Hola, ¿qué endpoints tienes?)",
                        lines=2,
                        scale=5,
                        label=""
                    )
                    enviar_btn = gr.Button("📤 Enviar", scale=1, variant="primary", size="lg")
                
                limpiar_btn = gr.Button("🗑️ Nueva conversación", variant="secondary")
            
            # PANEL LATERAL
            with gr.Column(scale=1):
                gr.Markdown("### 📄 Generar Documentación")
                
                with gr.Group():
                    carpeta_output = gr.Textbox(
                        label="📁 Carpeta de destino",
                        value=str(DOCS_OUTPUT_PATH),
                        placeholder="Ruta donde guardar el README.md"
                    )
                    
                    generar_readme_btn = gr.Button(
                        "📝 Generar README.md",
                        variant="primary",
                        size="lg"
                    )
                    
                    resultado_readme = gr.Markdown(
                        "",
                        elem_classes=["success-box"]
                    )
                
                gr.Markdown(f"""
                <div class="info-box">
                
                ### 💡 Sugerencias de Conversación
                
                **🎯 Para empezar:**
                - *"Hola, ¿qué puedes hacer?"*
                - *"Cuéntame sobre el proyecto"*
                
                **📋 Explorar endpoints:**
                - *"¿Qué endpoints tiene la API?"*
                - *"Muéstrame las rutas de autenticación"*
                
                **🔍 Código específico:**
                - *"¿Cómo funciona el login?"*
                - *"Explícame el endpoint /users"*
                
                **📚 Documentación:**
                - *"Genera un README completo"*
                - *"Documenta la estructura del proyecto"*
                
                ---
                
                ### 📊 Estado del Proyecto
                
                - **Endpoints:** {len(system.cache_endpoints)}
                - **Archivos:** {len(system.cache_archivos)}
                - **Routers:** {len(system.cache_routers)}
                
                </div>
                """)
        
        # ═══════════════════════════════════════════════════════════
        # EVENTOS Y LÓGICA
        # ═══════════════════════════════════════════════════════════
        
        def chat_handler(mensaje, historial, modelo):
            """Manejador principal del chat conversacional"""
            
            if not mensaje.strip():
                return historial, ""
            
            if modelo not in system.clients:
                historial.append((mensaje, f"❌ El modelo {modelo} no está disponible. Verifica tu configuración."))
                return historial, ""
            
            try:
                # ✅ SALUDO INICIAL (primera interacción)
                if not system.saludo_inicial_enviado and not historial:
                    system.saludo_inicial_enviado = True
                    saludo = system.generar_saludo_inicial()
                    historial.append((mensaje, saludo))
                    
                    # Guardar en historial
                    system.conversation_history.append({
                        'pregunta': mensaje,
                        'respuesta': saludo
                    })
                    
                    return historial, ""
                
                # ✅ DETECTAR TIPO DE PREGUNTA
                tipo_pregunta = system.detectar_tipo_pregunta(mensaje)
                print(f"\n🎯 Tipo detectado: {tipo_pregunta}")
                
                # ✅ CASO: Generar documentación
                if tipo_pregunta == 'GENERAR_DOC':
                    respuesta = """
¡Perfecto! Voy a generar un README.md completo y profesional para tu proyecto. 

📝 Usa el botón **"Generar README.md"** en el panel lateral, o si prefieres puedo ayudarte con documentación más específica.

¿Qué te gustaría documentar exactamente?
- 📄 README completo del proyecto
- 🌐 Documentación específica de endpoints
- 🔧 Guías de implementación
- 📚 Documentación técnica detallada
"""
                    historial.append((mensaje, respuesta))
                    system.conversation_history.append({
                        'pregunta': mensaje,
                        'respuesta': respuesta
                    })
                    return historial, ""
                
                # ✅ CASO: Lista de endpoints
                elif tipo_pregunta == 'LISTA':
                    endpoints = system.obtener_todos_endpoints()
                    codigo = None
                    print(f"📋 Búsqueda directa: {len(endpoints)} endpoints")
                
                # ✅ CASO: Código específico
                elif tipo_pregunta == 'CODIGO':
                    codigo = system.buscar_codigo_semantico(mensaje, top_k=5)
                    endpoints = None
                    print(f"🔍 Búsqueda semántica: {len(codigo)} resultados")
                
                # ✅ CASO: General
                else:
                    codigo = system.buscar_codigo_semantico(mensaje, top_k=3)
                    endpoints = None
                    print(f"💬 Búsqueda general")
                
                # Generar contexto técnico
                contexto_tecnico = system.generar_contexto_tecnico()
                
                # Crear prompt conversacional
                prompt = crear_prompt_conversacional_v4(
                    mensaje,
                    tipo_pregunta,
                    codigo,
                    endpoints,
                    contexto_tecnico,
                    system.conversation_history,
                    system.proyecto_nombre
                )
                
                # ✅ LLAMAR AL MODELO DE IA
                print(f"🤖 Generando respuesta con {modelo}...")
                
                if modelo == "GPT":
                    response = system.clients["GPT"].chat.completions.create(
                        model=MODEL_CONFIG["GPT"]["model"],
                        messages=[
                            {"role": "system", "content": "Eres un ingeniero senior experto y conversacional."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.4,
                        max_tokens=2500
                    )
                    respuesta = response.choices[0].message.content
                
                elif modelo == "Claude":
                    response = system.clients["Claude"].messages.create(
                        model=MODEL_CONFIG["Claude"]["model"],
                        max_tokens=2500,
                        temperature=0.4,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    respuesta = response.content[0].text
                
                elif modelo == "DeepSeek":
                    response = system.clients["DeepSeek"].chat.completions.create(
                        model=MODEL_CONFIG["DeepSeek"]["model"],
                        messages=[
                            {"role": "system", "content": "Eres un ingeniero senior experto y conversacional."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.4,
                        max_tokens=2500
                    )
                    respuesta = response.choices[0].message.content
                
                # Guardar en historial
                system.conversation_history.append({
                    'pregunta': mensaje,
                    'respuesta': respuesta
                })
                
                historial.append((mensaje, respuesta))
                print("✅ Respuesta generada")
                
                return historial, ""
            
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                
                error_msg = f"""
❌ **Ups, hubo un error...**

{str(e)}

Intenta reformular tu pregunta o verifica que:
- ✅ El modelo de IA esté correctamente configurado
- ✅ Tengas conexión a internet
- ✅ Las API keys sean válidas
"""
                historial.append((mensaje, error_msg))
                return historial, ""
        
        def generar_readme_handler(carpeta):
            """Manejador para generar README"""
            try:
                mensaje, path = system.generar_readme_completo(carpeta)
                return mensaje
            except Exception as e:
                return f"❌ Error: {str(e)}"
        
        def limpiar_chat():
            """Limpia el chat y reinicia la conversación"""
            system.conversation_history = []
            system.saludo_inicial_enviado = False
            return [], ""
        
        # Conectar eventos
        enviar_btn.click(
            fn=chat_handler,
            inputs=[mensaje_input, chatbot, modelo_ia],
            outputs=[chatbot, mensaje_input]
        )
        
        mensaje_input.submit(
            fn=chat_handler,
            inputs=[mensaje_input, chatbot, modelo_ia],
            outputs=[chatbot, mensaje_input]
        )
        
        generar_readme_btn.click(
            fn=generar_readme_handler,
            inputs=[carpeta_output],
            outputs=[resultado_readme]
        )
        
        limpiar_btn.click(
            fn=limpiar_chat,
            inputs=[],
            outputs=[chatbot, mensaje_input]
        )
    
    return interface


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 AGENTE DE DOCUMENTACIÓN V4 - CONVERSACIONAL")
    print("="*80 + "\n")
    
    print("✅ Saludo natural y contextual")
    print("✅ Personalidad conversacional como experto")
    print("✅ Generación de README.md profesional")
    print("✅ Búsqueda inteligente (directa + semántica)")
    print("✅ Interacción fluida y natural\n")
    
    interface = crear_interfaz()
    interface.launch(
        server_name="localhost",
        server_port=7865,
        share=False,
        show_error=True
    )