#!/usr/bin/env python3
"""
Enhanced Code Analyzer - Captura Dinámica de Endpoints
Escanea línea por línea para capturar TODOS los endpoints de FastAPI/Flask/Django
Versión: 4.0.0 - Mejora crítica de captura de endpoints
"""

import os
import re
import csv
import json
import ast
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
import traceback

# Configuración
RUTA_PROYECTO = "."
ARCHIVO_SALIDA_CSV = "datasets/documentacion.csv"
ARCHIVO_SALIDA_JSON = "datasets/analisis_mejorado.json"

# Carpetas raíces a buscar
CARPETAS_RAICES = ['app', 'src', 'backend', 'api', 'web', 'server', 'core']

# Carpetas a excluir
CARPETAS_EXCLUIR = {
    'venv', '.venv', 'env', '.env', '__pycache__', '.git', '.svn', '.hg',
    'node_modules', 'dist', 'build', 'target', '.pytest_cache',
    'alembic', 'migrations', 'static', 'templates', 'media',
    'logs', 'temp', 'tmp', 'cache', 'data', 'datasets'
}

# Extensiones permitidas
EXTENSIONES_PERMITIDAS = {'.py'}

# Campos completos para CSV
CAMPOS_CSV = [
    'tipo', 'ruta', 'nombre_archivo', 'elemento', 'categoria',
    'endpoint', 'metodo_http', 'descripcion', 'summary', 'description',
    'tags', 'response_model', 'status_code', 'decoradores',
    'parametros', 'parametros_query', 'parametros_path', 'parametros_body',
    'tipos_parametros', 'codigo_limpio', 'dependencias', 'tecnologias',
    'linea_inicio', 'numero_lineas', 'complejidad', 'imports',
    'router_padre', 'middlewares', 'event_handlers', 'include_routers',
    'responses', 'ejemplos', 'validaciones', 'es_async', 'es_decorador'
]

class EnhancedEndpointAnalyzer:
    def __init__(self, ruta_proyecto: str = "."):
        self.ruta_proyecto = ruta_proyecto
        self.estadisticas = {
            'total_archivos': 0,
            'archivos_procesados': 0,
            'archivos_con_errores': 0,
            'tipos_distribucion': {},
            'tecnologias_detectadas': set(),
            'endpoints_encontrados': 0,
            'endpoints_por_metodo': {},
            'clases_encontradas': 0,
            'funciones_encontradas': 0,
            'routers_detectados': 0,
            'routers_incluidos': 0
        }
        self.registros = []
        self.routers_padre = {}
        
    def extraer_endpoints_completos(self, contenido: str, nombre_archivo: str = "") -> List[Dict]:
        """
        Extrae endpoints línea por línea de forma DINÁMICA
        Captura TODOS los formatos de decoradores de endpoints
        """
        endpoints = []
        lineas = contenido.split('\n')
        
        # Patrones para capturar diferentes formatos de endpoints
        patrones_endpoints = [
            # @router.get("/path")
            r'@(\w+)\.(get|post|put|delete|patch|options|head|trace)\s*\(\s*["\']([^"\']+)["\']',
            # @router.get("/path/{param}")
            r'@(\w+)\.(get|post|put|delete|patch|options|head|trace)\s*\(\s*["\']([^"\'{}]+(?:\{[^}]+\})*[^"\']*)["\']',
            # @app.route("/path", methods=["GET"])
            r'@(\w+)\.route\s*\(\s*["\']([^"\']+)["\'][^)]*methods\s*=\s*\[\"([^\"]+)\"',
        ]
        
        endpoints_procesados = set()
        
        print(f"  📄 Analizando: {nombre_archivo}")
        
        for i, linea in enumerate(lineas):
            linea_limpia = linea.strip()
            
            if not linea_limpia.startswith('@'):
                continue
            
            # Probar todos los patrones
            endpoint_match = None
            metodo_http = None
            ruta_endpoint = None
            router_obj = None
            
            for patron in patrones_endpoints:
                match = re.search(patron, linea_limpia, re.IGNORECASE)
                if match:
                    if 'route' in patron:
                        # Flask: @app.route("/path", methods=["GET"])
                        router_obj = match.group(1)
                        ruta_endpoint = match.group(2)
                        metodo_http = match.group(3).upper()
                    else:
                        # FastAPI: @router.get("/path")
                        router_obj = match.group(1)
                        metodo_http = match.group(2).upper()
                        ruta_endpoint = match.group(3)
                    
                    endpoint_match = match
                    break
            
            if not endpoint_match:
                continue
            
            # Clave única para evitar duplicados
            endpoint_key = f"{metodo_http}:{ruta_endpoint}:{i}"
            if endpoint_key in endpoints_procesados:
                continue
            
            endpoints_procesados.add(endpoint_key)
            
            print(f"    🎯 Línea {i+1}: {metodo_http:6} {ruta_endpoint}")
            
            # Recolectar decoradores previos
            decoradores_previos = []
            j = i - 1
            while j >= 0:
                linea_prev = lineas[j].strip()
                if linea_prev.startswith('@'):
                    decoradores_previos.insert(0, linea_prev)
                    j -= 1
                elif linea_prev == '' or linea_prev.startswith('#'):
                    j -= 1
                else:
                    break
            
            # Buscar la función asociada
            funcion_info = self.buscar_funcion_completa(lineas, i)
            if not funcion_info:
                funcion_info = {
                    'nombre': f'endpoint_function_{i}',
                    'parametros': '',
                    'return_type': '',
                    'linea_inicio': i + 1,
                    'es_async': False,
                    'codigo_completo': linea_limpia
                }
            
            # Construir decorador completo (puede estar en múltiples líneas)
            decorador_completo = linea_limpia
            if '(' in decorador_completo and ')' not in decorador_completo:
                k = i + 1
                while k < len(lineas) and ')' not in lineas[k]:
                    decorador_completo += ' ' + lineas[k].strip()
                    k += 1
                if k < len(lineas):
                    decorador_completo += ' ' + lineas[k].strip()
            
            # Extraer información del decorador
            info_decorador = self.extraer_info_decorador_mejorado(decorador_completo)
            
            # Analizar parámetros
            parametros_info = self.extraer_parametros_detallados(funcion_info['parametros'])
            
            # Detectar router y prefix
            router_info = self.detectar_router_y_prefix(contenido, i)
            
            # Construir ruta completa
            ruta_completa = ruta_endpoint
            if router_info['prefix']:
                # Combinar prefix con ruta
                prefix = router_info['prefix'].rstrip('/')
                ruta_limpia = ruta_endpoint.lstrip('/')
                if ruta_limpia and not ruta_limpia.startswith(prefix):
                    ruta_completa = f"{prefix}/{ruta_limpia}"
            
            # Detectar middlewares
            middlewares = self.detectar_middlewares(decoradores_previos)
            
            # Crear registro del endpoint
            endpoint_data = {
                'metodo': metodo_http,
                'ruta': ruta_completa,
                'ruta_original': ruta_endpoint,
                'funcion': funcion_info['nombre'],
                'parametros': funcion_info['parametros'],
                'parametros_query': parametros_info['query'],
                'parametros_path': parametros_info['path'],
                'parametros_body': parametros_info['body'],
                'tipos_parametros': parametros_info['tipos'],
                'decorador': decorador_completo,
                'todos_decoradores': decoradores_previos + [decorador_completo],
                'linea': i + 1,
                'summary': info_decorador['summary'],
                'description': info_decorador['description'],
                'tags': info_decorador['tags'],
                'response_model': info_decorador['response_model'],
                'status_code': info_decorador['status_code'],
                'responses': info_decorador['responses'],
                'router_padre': router_info['router_name'],
                'router_prefix': router_info['prefix'],
                'router_tags': router_info['tags'],
                'middlewares': middlewares,
                'es_async': funcion_info['es_async'],
                'codigo_completo': funcion_info['codigo_completo']
            }
            
            endpoints.append(endpoint_data)
            
            # Actualizar estadísticas
            self.estadisticas['endpoints_por_metodo'][metodo_http] = \
                self.estadisticas['endpoints_por_metodo'].get(metodo_http, 0) + 1
        
        if endpoints:
            print(f"    ✅ Total endpoints encontrados: {len(endpoints)}")
        
        return endpoints
    
    def buscar_funcion_completa(self, lineas: List[str], linea_decorador: int) -> Optional[Dict]:
        """Busca la función completa después de un decorador"""
        for i in range(linea_decorador, min(linea_decorador + 20, len(lineas))):
            linea = lineas[i]
            
            # Buscar definición de función
            match = re.search(r'^(\s*)(async\s+)?def\s+(\w+)\s*\((.*?)\)(?:\s*->\s*([^:]+))?\s*:', linea)
            
            if match:
                indent_base = len(match.group(1))
                es_async = bool(match.group(2))
                nombre = match.group(3)
                parametros = match.group(4)
                return_type = match.group(5)
                
                # Capturar cuerpo de la función
                codigo_completo = [linea.rstrip()]
                
                for j in range(i + 1, len(lineas)):
                    linea_siguiente = lineas[j]
                    
                    if not linea_siguiente.strip():
                        codigo_completo.append('')
                        continue
                    
                    indent_actual = len(linea_siguiente) - len(linea_siguiente.lstrip())
                    
                    # Verificar si seguimos dentro de la función
                    if indent_actual > indent_base:
                        codigo_completo.append(linea_siguiente.rstrip())
                    elif linea_siguiente.strip() and (
                        indent_actual <= indent_base and
                        (linea_siguiente.strip().startswith(('def ', 'class ', '@')) or
                         indent_actual == 0)
                    ):
                        break
                
                return {
                    'nombre': nombre,
                    'parametros': parametros,
                    'return_type': return_type if return_type else '',
                    'linea_inicio': i + 1,
                    'es_async': es_async,
                    'codigo_completo': '\n'.join(codigo_completo)
                }
        
        return None
    
    def extraer_info_decorador_mejorado(self, decorador: str) -> Dict[str, Any]:
        """Extrae toda la información del decorador"""
        info = {
            'ruta': '',
            'summary': '',
            'description': '',
            'tags': [],
            'response_model': '',
            'status_code': '',
            'responses': [],
            'deprecated': False
        }
        
        # Ruta
        ruta_match = re.search(r'["\']([^"\']+)["\']', decorador)
        if ruta_match:
            info['ruta'] = ruta_match.group(1)
        
        # Summary
        summary_match = re.search(r'summary\s*=\s*["\']([^"\']+)["\']', decorador, re.IGNORECASE)
        if summary_match:
            info['summary'] = summary_match.group(1)
        
        # Description
        desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', decorador, re.IGNORECASE)
        if desc_match:
            info['description'] = desc_match.group(1)
        
        # Tags
        tags_match = re.search(r'tags\s*=\s*\[([^\]]+)\]', decorador, re.IGNORECASE)
        if tags_match:
            tags_str = tags_match.group(1)
            info['tags'] = [tag.strip().strip('"\'') for tag in tags_str.split(',') if tag.strip()]
        
        # Response model
        response_match = re.search(r'response_model\s*=\s*([^,\)]+)', decorador, re.IGNORECASE)
        if response_match:
            info['response_model'] = response_match.group(1).strip()
        
        # Status code
        status_match = re.search(r'status_code\s*=\s*(?:status\.)?HTTP_(\d+)', decorador, re.IGNORECASE)
        if status_match:
            info['status_code'] = status_match.group(1)
        else:
            status_match = re.search(r'status_code\s*=\s*(\d+)', decorador)
            if status_match:
                info['status_code'] = status_match.group(1)
        
        # Responses
        responses_match = re.search(r'responses\s*=\s*\{([^}]+)\}', decorador, re.IGNORECASE)
        if responses_match:
            info['responses'] = [responses_match.group(1).strip()]
        
        # Deprecated
        if 'deprecated' in decorador.lower():
            info['deprecated'] = True
        
        return info
    
    def detectar_router_y_prefix(self, contenido: str, linea_actual: int) -> Dict[str, Any]:
        """Detecta el router padre y su configuración"""
        router_info = {
            'router_name': '',
            'prefix': '',
            'tags': []
        }
        
        lineas = contenido.split('\n')
        contenido_previo = '\n'.join(lineas[:linea_actual])
        
        # Buscar declaraciones de router
        patron_router = r'(\w+)\s*=\s*(?:APIRouter|FastAPI|Blueprint)\s*\(([^)]*)\)'
        
        routers = []
        for match in re.finditer(patron_router, contenido_previo):
            nombre_router = match.group(1)
            parametros = match.group(2)
            linea_router = contenido_previo[:match.start()].count('\n')
            
            # Extraer prefix
            prefix = ''
            prefix_match = re.search(r'prefix\s*=\s*["\']([^"\']+)["\']', parametros)
            if prefix_match:
                prefix = prefix_match.group(1)
            
            # Extraer tags
            tags = []
            tags_match = re.search(r'tags\s*=\s*\[([^\]]+)\]', parametros)
            if tags_match:
                tags_str = tags_match.group(1)
                tags = [tag.strip().strip('"\'') for tag in tags_str.split(',')]
            
            routers.append({
                'nombre': nombre_router,
                'prefix': prefix,
                'tags': tags,
                'linea': linea_router
            })
        
        # Usar el router más cercano
        if routers:
            router_cercano = max(routers, key=lambda r: r['linea'])
            router_info['router_name'] = router_cercano['nombre']
            router_info['prefix'] = router_cercano['prefix']
            router_info['tags'] = router_cercano['tags']
        
        # Buscar include_router para prefixes adicionales
        patron_include = r'(?:app|main)\.include_router\s*\(\s*(\w+)\s*,\s*prefix\s*=\s*["\']([^"\']+)["\']'
        for match in re.finditer(patron_include, contenido):
            router_ref = match.group(1)
            prefix_include = match.group(2)
            
            if router_info['router_name'] == router_ref:
                if router_info['prefix']:
                    router_info['prefix'] = prefix_include.rstrip('/') + '/' + router_info['prefix'].lstrip('/')
                else:
                    router_info['prefix'] = prefix_include
        
        return router_info
    
    def extraer_parametros_detallados(self, parametros_funcion: str) -> Dict[str, Any]:
        """Extrae información detallada de parámetros"""
        info = {
            'query': [],
            'path': [],
            'body': [],
            'tipos': {}
        }
        
        if not parametros_funcion:
            return info
        
        params = [p.strip() for p in parametros_funcion.split(',')]
        
        for param in params:
            if not param or param in ['self', 'cls']:
                continue
            
            # Saltar dependencias
            if any(x in param for x in ['Depends(', 'Security(', 'Request', 'Response']):
                continue
            
            # Detectar tipo de parámetro
            if 'Query(' in param:
                query_match = re.search(r'(\w+)\s*:', param)
                if query_match:
                    info['query'].append(query_match.group(1))
            elif 'Path(' in param:
                path_match = re.search(r'(\w+)\s*:', param)
                if path_match:
                    info['path'].append(path_match.group(1))
            elif 'Body(' in param:
                body_match = re.search(r'(\w+)\s*:', param)
                if body_match:
                    info['body'].append(body_match.group(1))
            else:
                # Parámetro simple
                tipo_match = re.search(r'(\w+)\s*:\s*([\w\[\]\.]+)', param)
                if tipo_match:
                    nombre = tipo_match.group(1)
                    tipo = tipo_match.group(2)
                    info['tipos'][nombre] = tipo
                    
                    # Clasificar por tipo
                    if tipo in ['int', 'float', 'str', 'bool', 'Optional[str]', 'Optional[int]']:
                        info['query'].append(nombre)
                    elif 'Model' in tipo or 'Schema' in tipo or 'Create' in tipo or 'Update' in tipo:
                        info['body'].append(nombre)
                    else:
                        info['query'].append(nombre)
        
        return info
    
    def detectar_middlewares(self, decoradores: List[str]) -> List[str]:
        """Detecta middlewares en decoradores"""
        middlewares = []
        for dec in decoradores:
            if any(x in dec.lower() for x in ['middleware', 'before_request', 'after_request']):
                middlewares.append(dec)
        return middlewares
    
    # ==========================================
    # 🔍 SEGUNDA PASADA: EXTRACCIÓN AVANZADA
    # ==========================================
    
    def extraer_clases_avanzado(self, contenido: str, tipo_archivo: str, tecnologias: List[str]) -> List[Dict]:
        """
        Extrae TODAS las clases con análisis profundo:
        - Modelos SQLAlchemy/ORM
        - Schemas Pydantic
        - Excepciones personalizadas
        - Clases de servicio
        - Factories, Builders, etc.
        """
        clases = []
        
        try:
            tree = ast.parse(contenido)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Extraer información completa
                    clase_info = {
                        'nombre': node.name,
                        'linea_inicio': node.lineno,
                        'linea_fin': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 20,
                        'decoradores': [],
                        'herencia': [],
                        'atributos': [],
                        'metodos': [],
                        'validadores': [],
                        'relaciones': [],
                        'docstring': ast.get_docstring(node) or '',
                        'tipo_clase': 'class'
                    }
                    
                    # Extraer decoradores
                    for dec in node.decorator_list:
                        if hasattr(ast, 'unparse'):
                            clase_info['decoradores'].append(ast.unparse(dec))
                    
                    # Extraer herencia
                    for base in node.bases:
                        if hasattr(ast, 'unparse'):
                            base_name = ast.unparse(base)
                            clase_info['herencia'].append(base_name)
                            
                            # Determinar tipo de clase por herencia
                            if 'Base' in base_name or 'Model' in base_name:
                                if 'sqlalchemy' in tecnologias:
                                    clase_info['tipo_clase'] = 'model_orm'
                            elif 'BaseModel' in base_name:
                                if 'pydantic' in tecnologias:
                                    clase_info['tipo_clase'] = 'schema_pydantic'
                            elif 'Exception' in base_name or 'Error' in base_name:
                                clase_info['tipo_clase'] = 'exception'
                    
                    # Extraer atributos y métodos
                    for item in node.body:
                        # ATRIBUTOS
                        if isinstance(item, ast.AnnAssign):
                            attr_name = item.target.id if hasattr(item.target, 'id') else str(item.target)
                            attr_tipo = ast.unparse(item.annotation) if hasattr(ast, 'unparse') else ''
                            attr_default = ast.unparse(item.value) if item.value and hasattr(ast, 'unparse') else ''
                            
                            atributo = {
                                'nombre': attr_name,
                                'tipo': attr_tipo,
                                'default': attr_default,
                                'linea': item.lineno
                            }
                            
                            # Detectar relaciones ORM
                            if 'relationship' in attr_default.lower() or 'Mapped' in attr_tipo:
                                clase_info['relaciones'].append(atributo)
                            
                            clase_info['atributos'].append(atributo)
                        
                        # ASIGNACIONES SIMPLES (ej: name = "default")
                        elif isinstance(item, ast.Assign):
                            for target in item.targets:
                                if isinstance(target, ast.Name):
                                    valor = ast.unparse(item.value) if hasattr(ast, 'unparse') else ''
                                    clase_info['atributos'].append({
                                        'nombre': target.id,
                                        'tipo': '',
                                        'default': valor,
                                        'linea': item.lineno
                                    })
                        
                        # MÉTODOS
                        elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            metodo = {
                                'nombre': item.name,
                                'parametros': [arg.arg for arg in item.args.args if arg.arg != 'self'],
                                'es_async': isinstance(item, ast.AsyncFunctionDef),
                                'decoradores': [ast.unparse(d) for d in item.decorator_list] if hasattr(ast, 'unparse') else [],
                                'linea': item.lineno,
                                'docstring': ast.get_docstring(item) or ''
                            }
                            
                            # Detectar validadores Pydantic
                            if any('validator' in str(d).lower() or 'field_validator' in str(d).lower() for d in item.decorator_list):
                                clase_info['validadores'].append(metodo)
                            
                            # Detectar métodos especiales
                            if item.name.startswith('__') and item.name.endswith('__'):
                                metodo['tipo_metodo'] = 'magic'
                            elif item.name.startswith('_'):
                                metodo['tipo_metodo'] = 'private'
                            elif any(d in metodo['decoradores'] for d in ['@property', '@staticmethod', '@classmethod']):
                                metodo['tipo_metodo'] = 'special'
                            else:
                                metodo['tipo_metodo'] = 'public'
                            
                            clase_info['metodos'].append(metodo)
                    
                    clase_info['numero_lineas'] = clase_info['linea_fin'] - clase_info['linea_inicio'] + 1
                    clases.append(clase_info)
                    
        except Exception as e:
            print(f"    ⚠️  Error parseando clases con AST: {e}")
            # Fallback a regex si falla AST
            clases = self.extraer_clases_regex_avanzado(contenido)
        
        return clases
    
    def extraer_clases_regex_avanzado(self, contenido: str) -> List[Dict]:
        """Fallback: Extrae clases usando regex cuando AST falla"""
        clases = []
        patron_clase = r'class\s+(\w+)\s*(?:\(([^)]*)\))?\s*:'
        
        for match in re.finditer(patron_clase, contenido):
            nombre = match.group(1)
            herencia = match.group(2) if match.group(2) else ''
            linea_inicio = contenido[:match.start()].count('\n') + 1
            
            # Extraer docstring
            docstring = ''
            docstring_match = re.search(
                rf'class\s+{nombre}[^:]*:\s*"""([^"]+)"""',
                contenido[match.start():match.start()+500],
                re.DOTALL
            )
            if docstring_match:
                docstring = docstring_match.group(1).strip()
            
            clases.append({
                'nombre': nombre,
                'linea_inicio': linea_inicio,
                'linea_fin': linea_inicio + 30,
                'decoradores': [],
                'herencia': [h.strip() for h in herencia.split(',')] if herencia else [],
                'atributos': [],
                'metodos': [],
                'validadores': [],
                'relaciones': [],
                'docstring': docstring,
                'tipo_clase': 'class',
                'numero_lineas': 30
            })
        
        return clases
    
    def extraer_funciones_avanzado(self, contenido: str, tipo_archivo: str) -> List[Dict]:
        """
        Extrae TODAS las funciones con análisis profundo:
        - Servicios y lógica de negocio
        - Utilidades y helpers
        - Validadores y transformadores
        - Factories y builders
        - Middlewares y decoradores
        """
        funciones = []
        
        try:
            tree = ast.parse(contenido)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Saltar métodos de clase (ya capturados en clases)
                    es_metodo = False
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef):
                            if node in parent.body:
                                es_metodo = True
                                break
                    
                    if es_metodo:
                        continue
                    
                    # Extraer información completa
                    funcion_info = {
                        'nombre': node.name,
                        'linea_inicio': node.lineno,
                        'linea_fin': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno + 10,
                        'es_async': isinstance(node, ast.AsyncFunctionDef),
                        'decoradores': [],
                        'parametros': [],
                        'return_type': '',
                        'docstring': ast.get_docstring(node) or '',
                        'complejidad_local': 0,
                        'tipo_funcion': 'function'
                    }
                    
                    # Extraer decoradores
                    for dec in node.decorator_list:
                        if hasattr(ast, 'unparse'):
                            dec_str = ast.unparse(dec)
                            funcion_info['decoradores'].append(dec_str)
                            
                            # Determinar tipo de función por decorador
                            if 'Depends' in dec_str:
                                funcion_info['tipo_funcion'] = 'dependency'
                            elif any(x in dec_str.lower() for x in ['cache', 'lru_cache', 'memoize']):
                                funcion_info['tipo_funcion'] = 'cached'
                            elif any(x in dec_str.lower() for x in ['validate', 'validator']):
                                funcion_info['tipo_funcion'] = 'validator'
                    
                    # Extraer parámetros con tipos
                    for arg in node.args.args:
                        param = {
                            'nombre': arg.arg,
                            'tipo': ast.unparse(arg.annotation) if arg.annotation and hasattr(ast, 'unparse') else '',
                            'default': ''
                        }
                        funcion_info['parametros'].append(param)
                    
                    # Añadir defaults
                    if node.args.defaults:
                        defaults_start = len(funcion_info['parametros']) - len(node.args.defaults)
                        for i, default in enumerate(node.args.defaults):
                            if defaults_start + i < len(funcion_info['parametros']):
                                funcion_info['parametros'][defaults_start + i]['default'] = \
                                    ast.unparse(default) if hasattr(ast, 'unparse') else ''
                    
                    # Return type
                    if node.returns:
                        funcion_info['return_type'] = ast.unparse(node.returns) if hasattr(ast, 'unparse') else ''
                    
                    # Calcular complejidad local
                    funcion_info['complejidad_local'] = self.calcular_complejidad_funcion(node)
                    
                    # Detectar tipo por nombre y contexto
                    nombre_lower = node.name.lower()
                    if nombre_lower.startswith('get_'):
                        funcion_info['tipo_funcion'] = 'getter'
                    elif nombre_lower.startswith(('create_', 'make_', 'build_')):
                        funcion_info['tipo_funcion'] = 'factory'
                    elif nombre_lower.startswith(('validate_', 'check_', 'verify_')):
                        funcion_info['tipo_funcion'] = 'validator'
                    elif nombre_lower.startswith(('handle_', 'process_')):
                        funcion_info['tipo_funcion'] = 'handler'
                    elif nombre_lower.startswith(('format_', 'transform_', 'convert_')):
                        funcion_info['tipo_funcion'] = 'transformer'
                    
                    funcion_info['numero_lineas'] = funcion_info['linea_fin'] - funcion_info['linea_inicio'] + 1
                    funciones.append(funcion_info)
                    
        except Exception as e:
            print(f"    ⚠️  Error parseando funciones con AST: {e}")
            funciones = self.extraer_funciones_regex_avanzado(contenido)
        
        return funciones
    
    def extraer_funciones_regex_avanzado(self, contenido: str) -> List[Dict]:
        """Fallback: Extrae funciones usando regex"""
        funciones = []
        patron = r'(?:async\s+)?def\s+(\w+)\s*\((.*?)\)(?:\s*->\s*([^:]+))?\s*:'
        
        for match in re.finditer(patron, contenido, re.DOTALL):
            nombre = match.group(1)
            if nombre.startswith('_') and not nombre.startswith('__'):
                continue  # Saltar funciones privadas internas
            
            parametros = match.group(2) if match.group(2) else ''
            return_type = match.group(3) if match.group(3) else ''
            linea_inicio = contenido[:match.start()].count('\n') + 1
            
            funciones.append({
                'nombre': nombre,
                'linea_inicio': linea_inicio,
                'linea_fin': linea_inicio + 15,
                'es_async': 'async' in match.group(0),
                'decoradores': [],
                'parametros': self.parsear_parametros_simple(parametros),
                'return_type': return_type.strip() if return_type else '',
                'docstring': '',
                'complejidad_local': 1,
                'tipo_funcion': 'function',
                'numero_lineas': 15
            })
        
        return funciones
    
    def parsear_parametros_simple(self, parametros_str: str) -> List[Dict]:
        """Parsea string de parámetros de forma simple"""
        params = []
        for param in parametros_str.split(','):
            param = param.strip()
            if param and ':' in param:
                partes = param.split(':', 1)
                nombre = partes[0].strip()
                tipo = partes[1].split('=')[0].strip() if '=' in partes[1] else partes[1].strip()
                default = partes[1].split('=')[1].strip() if '=' in partes[1] else ''
                params.append({'nombre': nombre, 'tipo': tipo, 'default': default})
            elif param:
                params.append({'nombre': param, 'tipo': '', 'default': ''})
        return params
    
    def calcular_complejidad_funcion(self, node: ast.FunctionDef) -> int:
        """Calcula complejidad ciclomática de una función específica"""
        complejidad = 1
        for subnode in ast.walk(node):
            if isinstance(subnode, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complejidad += 1
            elif isinstance(subnode, ast.BoolOp):
                complejidad += len(subnode.values) - 1
        return complejidad
    
    def extraer_configuraciones(self, contenido: str, tipo_archivo: str) -> List[Dict]:
        """
        Extrae configuraciones, constantes y variables globales:
        - Settings y configuraciones
        - Constantes (UPPER_CASE)
        - Variables de entorno
        - URLs y endpoints base
        """
        configuraciones = []
        
        # Buscar asignaciones de nivel módulo
        try:
            tree = ast.parse(contenido)
            
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            nombre = target.id
                            valor = ast.unparse(node.value) if hasattr(ast, 'unparse') else ''
                            
                            # Solo capturar constantes o configuraciones importantes
                            if nombre.isupper() or any(x in nombre.lower() for x in ['config', 'setting', 'url', 'key', 'secret', 'env']):
                                configuraciones.append({
                                    'nombre': nombre,
                                    'valor': valor if len(valor) < 200 else valor[:200] + '...',
                                    'tipo': 'CONSTANT' if nombre.isupper() else 'VARIABLE',
                                    'linea': node.lineno
                                })
                
                # Clases de configuración (ej: Settings, Config)
                elif isinstance(node, ast.ClassDef):
                    if any(x in node.name.lower() for x in ['config', 'settings', 'env']):
                        configuraciones.append({
                            'nombre': node.name,
                            'valor': 'Configuration Class',
                            'tipo': 'CONFIG_CLASS',
                            'linea': node.lineno
                        })
                        
        except Exception as e:
            print(f"    ⚠️  Error extrayendo configuraciones: {e}")
        
        return configuraciones
    
    def extraer_dependencias_inyeccion(self, contenido: str) -> List[Dict]:
        """
        Extrae funciones de inyección de dependencias:
        - Funciones con Depends()
        - Factories de dependencias
        - Context managers
        """
        dependencias = []
        
        # Buscar funciones que devuelven dependencias
        patron_depends = r'def\s+(\w+)\s*\([^)]*\)(?:\s*->\s*([^:]+))?:\s*["\']?["\']?[^"]*yield'
        
        for match in re.finditer(patron_depends, contenido, re.DOTALL):
            nombre = match.group(1)
            return_type = match.group(2) if match.group(2) else ''
            linea = contenido[:match.start()].count('\n') + 1
            
            dependencias.append({
                'nombre': nombre,
                'return_type': return_type.strip() if return_type else '',
                'tipo': 'DEPENDENCY_INJECTION',
                'linea': linea,
                'es_generator': True
            })
        
        return dependencias
    
    # ==========================================
    # 📝 CREACIÓN DE REGISTROS
    # ==========================================
    
    def crear_registro_clase(self, clase: Dict, ruta: Path, tipo: str, tecnologias: List[str], 
                            imports: List[str], complejidad: int, include_routers: List) -> Dict:
        """Crea un registro completo para una clase"""
        
        # Construir descripción rica
        descripcion = f"Clase {clase['nombre']}"
        if clase['herencia']:
            descripcion += f" (hereda: {', '.join(clase['herencia'][:3])})"
        
        # Información detallada
        detalles = []
        if clase['atributos']:
            detalles.append(f"{len(clase['atributos'])} atributos")
        if clase['metodos']:
            detalles.append(f"{len(clase['metodos'])} métodos")
        if clase['validadores']:
            detalles.append(f"{len(clase['validadores'])} validadores")
        if clase['relaciones']:
            detalles.append(f"{len(clase['relaciones'])} relaciones ORM")
        
        description_completa = ' | '.join(detalles)
        if clase['docstring']:
            description_completa = clase['docstring'][:200] + " | " + description_completa
        
        # Extraer código de la clase
        codigo = self.extraer_codigo_elemento(ruta, clase['linea_inicio'], clase['linea_fin'])
        
        # Tipos de parámetros (atributos con tipos)
        tipos_attrs = {attr['nombre']: attr['tipo'] for attr in clase['atributos'] if attr['tipo']}
        
        return {
            'tipo': clase['tipo_clase'],
            'ruta': str(ruta),
            'nombre_archivo': ruta.name,
            'elemento': clase['nombre'],
            'categoria': 'CLASS',
            'endpoint': '',
            'metodo_http': '',
            'descripcion': descripcion,
            'summary': clase['docstring'][:100] if clase['docstring'] else '',
            'description': description_completa,
            'tags': ', '.join(clase['herencia'][:2]),
            'response_model': '',
            'status_code': '',
            'decoradores': ' | '.join(clase['decoradores']),
            'parametros': ', '.join([attr['nombre'] for attr in clase['atributos'][:10]]),
            'parametros_query': '',
            'parametros_path': '',
            'parametros_body': ','.join([attr['nombre'] for attr in clase['atributos'] if 'Model' in attr.get('tipo', '') or 'Schema' in attr.get('tipo', '')]),
            'tipos_parametros': json.dumps(tipos_attrs) if tipos_attrs else '',
            'codigo_limpio': codigo,
            'dependencias': ', '.join([attr['tipo'] for attr in clase['relaciones']][:5]),
            'tecnologias': ', '.join(tecnologias),
            'linea_inicio': clase['linea_inicio'],
            'numero_lineas': clase['numero_lineas'],
            'complejidad': complejidad,
            'imports': ', '.join(imports[:10]),
            'router_padre': '',
            'middlewares': '',
            'event_handlers': '',
            'include_routers': json.dumps(include_routers),
            'responses': '',
            'ejemplos': '',
            'validaciones': ', '.join([v['nombre'] for v in clase['validadores']]),
            'es_async': False,
            'es_decorador': False
        }
    
    def crear_registro_funcion(self, funcion: Dict, ruta: Path, tipo: str, tecnologias: List[str],
                              imports: List[str], complejidad: int, include_routers: List) -> Dict:
        """Crea un registro completo para una función"""
        
        # Construir descripción
        params_str = ', '.join([f"{p['nombre']}: {p['tipo']}" for p in funcion['parametros'] if p['tipo']][:3])
        if not params_str:
            params_str = ', '.join([p['nombre'] for p in funcion['parametros']][:3])
        
        descripcion = f"{'Async ' if funcion['es_async'] else ''}Función {funcion['nombre']}({params_str})"
        if funcion['return_type']:
            descripcion += f" -> {funcion['return_type']}"
        
        # Descripción detallada
        description_completa = f"Tipo: {funcion['tipo_funcion']} | Complejidad: {funcion['complejidad_local']}"
        if funcion['docstring']:
            description_completa = funcion['docstring'][:200] + " | " + description_completa
        
        # Código de la función
        codigo = self.extraer_codigo_elemento(ruta, funcion['linea_inicio'], funcion['linea_fin'])
        
        # Tipos de parámetros
        tipos_params = {p['nombre']: p['tipo'] for p in funcion['parametros'] if p['tipo']}
        
        return {
            'tipo': funcion['tipo_funcion'],
            'ruta': str(ruta),
            'nombre_archivo': ruta.name,
            'elemento': funcion['nombre'],
            'categoria': 'FUNCTION',
            'endpoint': '',
            'metodo_http': '',
            'descripcion': descripcion,
            'summary': funcion['docstring'][:100] if funcion['docstring'] else '',
            'description': description_completa,
            'tags': ', '.join(funcion['decoradores'][:2]),
            'response_model': funcion['return_type'],
            'status_code': '',
            'decoradores': ' | '.join(funcion['decoradores']),
            'parametros': ', '.join([p['nombre'] for p in funcion['parametros']]),
            'parametros_query': ', '.join([p['nombre'] for p in funcion['parametros'] if p['tipo'] in ['int', 'str', 'bool', 'float']]),
            'parametros_path': '',
            'parametros_body': ', '.join([p['nombre'] for p in funcion['parametros'] if 'Model' in p.get('tipo', '') or 'Schema' in p.get('tipo', '')]),
            'tipos_parametros': json.dumps(tipos_params) if tipos_params else '',
            'codigo_limpio': codigo,
            'dependencias': '',
            'tecnologias': ', '.join(tecnologias),
            'linea_inicio': funcion['linea_inicio'],
            'numero_lineas': funcion['numero_lineas'],
            'complejidad': funcion['complejidad_local'],
            'imports': ', '.join(imports[:10]),
            'router_padre': '',
            'middlewares': '',
            'event_handlers': '',
            'include_routers': json.dumps(include_routers),
            'responses': '',
            'ejemplos': '',
            'validaciones': '',
            'es_async': funcion['es_async'],
            'es_decorador': any('decorator' in d.lower() for d in funcion['decoradores'])
        }
    
    def crear_registro_configuracion(self, config: Dict, ruta: Path, tipo: str, 
                                    tecnologias: List[str], imports: List[str], complejidad: int) -> Dict:
        """Crea un registro para una configuración"""
        
        descripcion = f"{config['tipo']}: {config['nombre']}"
        if config['valor'] and config['valor'] != 'Configuration Class':
            descripcion += f" = {config['valor'][:50]}"
        
        return {
            'tipo': 'config',
            'ruta': str(ruta),
            'nombre_archivo': ruta.name,
            'elemento': config['nombre'],
            'categoria': config['tipo'],
            'endpoint': '',
            'metodo_http': '',
            'descripcion': descripcion,
            'summary': f"{config['tipo']} variable",
            'description': f"Valor: {config['valor']}",
            'tags': config['tipo'],
            'response_model': '',
            'status_code': '',
            'decoradores': '',
            'parametros': '',
            'parametros_query': '',
            'parametros_path': '',
            'parametros_body': '',
            'tipos_parametros': '',
            'codigo_limpio': f"{config['nombre']} = {config['valor']}",
            'dependencias': '',
            'tecnologias': ', '.join(tecnologias),
            'linea_inicio': config['linea'],
            'numero_lineas': 1,
            'complejidad': 1,
            'imports': ', '.join(imports[:10]),
            'router_padre': '',
            'middlewares': '',
            'event_handlers': '',
            'include_routers': '',
            'responses': '',
            'ejemplos': '',
            'validaciones': '',
            'es_async': False,
            'es_decorador': False
        }
    
    def crear_registro_dependencia(self, dep: Dict, ruta: Path, tipo: str,
                                   tecnologias: List[str], imports: List[str], complejidad: int) -> Dict:
        """Crea un registro para una dependencia de inyección"""
        
        descripcion = f"Dependency: {dep['nombre']}"
        if dep['return_type']:
            descripcion += f" -> {dep['return_type']}"
        
        return {
            'tipo': 'dependency',
            'ruta': str(ruta),
            'nombre_archivo': ruta.name,
            'elemento': dep['nombre'],
            'categoria': dep['tipo'],
            'endpoint': '',
            'metodo_http': '',
            'descripcion': descripcion,
            'summary': 'Dependency Injection',
            'description': f"Generator dependency returning {dep['return_type']}",
            'tags': 'dependency',
            'response_model': dep['return_type'],
            'status_code': '',
            'decoradores': '',
            'parametros': '',
            'parametros_query': '',
            'parametros_path': '',
            'parametros_body': '',
            'tipos_parametros': '',
            'codigo_limpio': f"def {dep['nombre']}(): yield ...",
            'dependencias': '',
            'tecnologias': ', '.join(tecnologias),
            'linea_inicio': dep['linea'],
            'numero_lineas': 5,
            'complejidad': 1,
            'imports': ', '.join(imports[:10]),
            'router_padre': '',
            'middlewares': '',
            'event_handlers': '',
            'include_routers': '',
            'responses': '',
            'ejemplos': '',
            'validaciones': '',
            'es_async': False,
            'es_decorador': False
        }
    
    def crear_registro_archivo_basico(self, contenido: str, ruta: Path, tipo: str,
                                      tecnologias: List[str], imports: List[str], complejidad: int) -> Dict:
        """Crea un registro básico cuando no se encuentra contenido específico"""
        
        num_lineas = len(contenido.split('\n'))
        preview = contenido[:500].strip() + ('...' if len(contenido) > 500 else '')
        
        return {
            'tipo': tipo,
            'ruta': str(ruta),
            'nombre_archivo': ruta.name,
            'elemento': ruta.stem,
            'categoria': 'FILE',
            'endpoint': '',
            'metodo_http': '',
            'descripcion': f"Archivo Python: {ruta.name}",
            'summary': f"Módulo con {num_lineas} líneas",
            'description': f"Imports: {len(imports)} | Tecnologías: {', '.join(tecnologias[:3])}",
            'tags': tipo,
            'response_model': '',
            'status_code': '',
            'decoradores': '',
            'parametros': '',
            'parametros_query': '',
            'parametros_path': '',
            'parametros_body': '',
            'tipos_parametros': '',
            'codigo_limpio': preview,
            'dependencias': '',
            'tecnologias': ', '.join(tecnologias),
            'linea_inicio': 1,
            'numero_lineas': num_lineas,
            'complejidad': complejidad,
            'imports': ', '.join(imports[:10]),
            'router_padre': '',
            'middlewares': '',
            'event_handlers': '',
            'include_routers': '',
            'responses': '',
            'ejemplos': '',
            'validaciones': '',
            'es_async': False,
            'es_decorador': False
        }
    
    def extraer_codigo_elemento(self, ruta: Path, linea_inicio: int, linea_fin: int) -> str:
        """Extrae el código de un elemento específico del archivo"""
        try:
            with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
                lineas = f.readlines()
            
            inicio = max(0, linea_inicio - 1)
            fin = min(len(lineas), linea_fin)
            
            codigo = ''.join(lineas[inicio:fin])
            
            # Limitar tamaño para el CSV
            if len(codigo) > 2000:
                codigo = codigo[:2000] + '\n... (truncado)'
            
            return codigo
        except Exception as e:
            return f"# Error extrayendo código: {e}"
    
    def detectar_tipo_archivo_inteligente(self, ruta_archivo: str, contenido: str) -> str:
        """Detecta el tipo de archivo"""
        ruta = Path(ruta_archivo)
        nombre = ruta.name.lower()
        partes_ruta = [p.lower() for p in ruta.parts]
        
        # Detectar por contenido
        if any(x in contenido for x in ['@router.', '@app.', '@bp.']):
            return 'route'
        if 'APIRouter' in contenido or 'api_router' in contenido:
            return 'router'
        
        # Detectar por ubicación
        if any('route' in parte for parte in partes_ruta):
            return 'route'
        elif any('model' in parte for parte in partes_ruta):
            return 'model'
        elif any('schema' in parte for parte in partes_ruta):
            return 'schema'
        elif 'main' in nombre or 'app' in nombre:
            return 'main'
        
        return 'util'
    
    def extraer_imports(self, contenido: str) -> List[str]:
        """Extrae imports del código"""
        imports = []
        try:
            tree = ast.parse(contenido)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
        except:
            import_lines = re.findall(r'^(?:from|import)\s+(\w+(?:\.\w+)*)', contenido, re.MULTILINE)
            imports.extend(import_lines)
        return imports
    
    def detectar_tecnologias(self, contenido: str, imports: List[str]) -> List[str]:
        """Detecta tecnologías usadas"""
        tecnologias = []
        contenido_lower = contenido.lower()
        
        if 'fastapi' in contenido_lower:
            tecnologias.append('fastapi')
        if 'flask' in contenido_lower:
            tecnologias.append('flask')
        if 'django' in contenido_lower:
            tecnologias.append('django')
        if 'sqlalchemy' in contenido_lower:
            tecnologias.append('sqlalchemy')
        if 'pydantic' in contenido_lower:
            tecnologias.append('pydantic')
        if 'jwt' in contenido_lower:
            tecnologias.append('jwt')
        
        return list(set(tecnologias))
    
    def calcular_complejidad_ciclomatica(self, contenido: str) -> int:
        """Calcula complejidad ciclomática básica"""
        complejidad = 1
        complejidad += len(re.findall(r'\bif\s+', contenido))
        complejidad += len(re.findall(r'\belif\s+', contenido))
        complejidad += len(re.findall(r'\bfor\s+', contenido))
        complejidad += len(re.findall(r'\bwhile\s+', contenido))
        complejidad += len(re.findall(r'\btry\s*:', contenido))
        complejidad += len(re.findall(r'\bexcept\s+', contenido))
        return complejidad
    
    def detectar_include_routers(self, contenido: str) -> List[Dict]:
        """Detecta llamadas a include_router"""
        include_routers = []
        patron = r'\.(include_router|include)\s*\(([^)]+)\)'
        
        for match in re.finditer(patron, contenido):
            parametros = match.group(2)
            
            router_match = re.search(r'(\w+)(?:,|\))', parametros)
            prefix_match = re.search(r'prefix\s*=\s*["\']([^"\']+)["\']', parametros)
            tags_match = re.search(r'tags\s*=\s*\[([^\]]+)\]', parametros)
            
            include_routers.append({
                'router': router_match.group(1) if router_match else '',
                'prefix': prefix_match.group(1) if prefix_match else '',
                'tags': tags_match.group(1) if tags_match else '',
                'linea': contenido[:match.start()].count('\n') + 1
            })
            
            self.estadisticas['routers_incluidos'] += 1
        
        return include_routers
    
    def procesar_archivo(self, ruta_archivo: str) -> List[Dict]:
        """
        Procesa un archivo Python completo con DOBLE ANÁLISIS:
        1. PRIMERA PASADA: Captura endpoints (YA FUNCIONA ✅)
        2. SEGUNDA PASADA: Captura TODO lo demás (modelos, schemas, funciones, etc.)
        """
        registros = []
        
        try:
            with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                contenido = f.read()
            
            if not contenido.strip():
                return registros
            
            ruta = Path(ruta_archivo)
            imports = self.extraer_imports(contenido)
            tipo = self.detectar_tipo_archivo_inteligente(ruta_archivo, contenido)
            tecnologias = self.detectar_tecnologias(contenido, imports)
            complejidad = self.calcular_complejidad_ciclomatica(contenido)
            
            self.estadisticas['total_archivos'] += 1
            self.estadisticas['tipos_distribucion'][tipo] = \
                self.estadisticas['tipos_distribucion'].get(tipo, 0) + 1
            self.estadisticas['tecnologias_detectadas'].update(tecnologias)
            
            # Detectar include_routers
            include_routers = self.detectar_include_routers(contenido)
            
            # ==========================================
            # 🎯 PRIMERA PASADA: ENDPOINTS (YA FUNCIONA)
            # ==========================================
            endpoints = self.extraer_endpoints_completos(contenido, ruta.name)
            
            if endpoints:
                for endpoint in endpoints:
                    descripcion = f"{endpoint['metodo']} {endpoint['ruta']}"
                    if endpoint['summary']:
                        descripcion += f" - {endpoint['summary']}"
                    
                    # Extraer dependencias
                    dependencias = []
                    for dec in endpoint['todos_decoradores']:
                        if 'Depends(' in dec:
                            dep_match = re.search(r'Depends\(([^)]+)\)', dec)
                            if dep_match:
                                dependencias.append(dep_match.group(1).strip())
                    
                    registros.append({
                        'tipo': 'route',
                        'ruta': str(ruta),
                        'nombre_archivo': ruta.name,
                        'elemento': endpoint['funcion'],
                        'categoria': 'ENDPOINT',
                        'endpoint': endpoint['ruta'],  # ✅ CRÍTICO
                        'metodo_http': endpoint['metodo'],  # ✅ CRÍTICO
                        'descripcion': descripcion,
                        'summary': endpoint['summary'],
                        'description': endpoint['description'],
                        'tags': ', '.join(endpoint['tags'] + endpoint.get('router_tags', [])),
                        'response_model': endpoint['response_model'],
                        'status_code': endpoint['status_code'],
                        'decoradores': ' | '.join(endpoint['todos_decoradores']),
                        'parametros': endpoint['parametros'],
                        'parametros_query': ', '.join(endpoint['parametros_query']),
                        'parametros_path': ', '.join(endpoint['parametros_path']),
                        'parametros_body': ', '.join(endpoint['parametros_body']),
                        'tipos_parametros': json.dumps(endpoint['tipos_parametros']) if endpoint['tipos_parametros'] else '',
                        'codigo_limpio': endpoint['codigo_completo'],
                        'dependencias': ', '.join(dependencias),
                        'tecnologias': ', '.join(tecnologias),
                        'linea_inicio': endpoint['linea'],
                        'numero_lineas': len(endpoint['codigo_completo'].split('\n')),
                        'complejidad': complejidad,
                        'imports': ', '.join(imports[:10]),
                        'router_padre': endpoint['router_padre'],
                        'middlewares': ', '.join(endpoint['middlewares']),
                        'event_handlers': '',
                        'include_routers': json.dumps(include_routers),
                        'responses': ', '.join(endpoint['responses']),
                        'ejemplos': '',
                        'validaciones': '',
                        'es_async': endpoint['es_async'],
                        'es_decorador': False
                    })
                
                self.estadisticas['endpoints_encontrados'] += len(endpoints)
            
            # ==========================================
            # 🔍 SEGUNDA PASADA: TODO LO DEMÁS
            # ==========================================
            # Extraer CLASES (Modelos, Schemas, Excepciones, etc.)
            clases = self.extraer_clases_avanzado(contenido, tipo, tecnologias)
            for clase in clases:
                self.estadisticas['clases_encontradas'] += 1
                registros.append(self.crear_registro_clase(clase, ruta, tipo, tecnologias, imports, complejidad, include_routers))
            
            # Extraer FUNCIONES (Servicios, Utils, Helpers, etc.)
            funciones = self.extraer_funciones_avanzado(contenido, tipo)
            # Filtrar funciones que ya están como endpoints
            funciones_nombres_endpoints = {ep['funcion'] for ep in endpoints}
            funciones_filtradas = [f for f in funciones if f['nombre'] not in funciones_nombres_endpoints]
            
            for funcion in funciones_filtradas:
                self.estadisticas['funciones_encontradas'] += 1
                registros.append(self.crear_registro_funcion(funcion, ruta, tipo, tecnologias, imports, complejidad, include_routers))
            
            # Extraer CONFIGURACIONES (Variables, Constantes, Settings)
            configuraciones = self.extraer_configuraciones(contenido, tipo)
            for config in configuraciones:
                registros.append(self.crear_registro_configuracion(config, ruta, tipo, tecnologias, imports, complejidad))
            
            # Extraer DEPENDENCIAS (Dependency Injection, Factories)
            dependencias_di = self.extraer_dependencias_inyeccion(contenido)
            for dep in dependencias_di:
                registros.append(self.crear_registro_dependencia(dep, ruta, tipo, tecnologias, imports, complejidad))
            
            # Si NO se encontró nada, crear registro básico del archivo
            if not registros:
                registros.append(self.crear_registro_archivo_basico(contenido, ruta, tipo, tecnologias, imports, complejidad))
            
            self.estadisticas['archivos_procesados'] += 1
            
        except Exception as e:
            print(f"✗ Error procesando {ruta_archivo}: {e}")
            self.estadisticas['archivos_con_errores'] += 1
            traceback.print_exc()
        
        return registros
    
    def encontrar_carpeta_raiz(self) -> str:
        """Encuentra la carpeta raíz del proyecto"""
        for carpeta in CARPETAS_RAICES:
            ruta_completa = os.path.join(self.ruta_proyecto, carpeta)
            if os.path.exists(ruta_completa) and os.path.isdir(ruta_completa):
                return ruta_completa
        return self.ruta_proyecto
    
    def deberia_procesar_archivo(self, ruta_archivo: str) -> bool:
        """Verifica si un archivo debe procesarse"""
        ruta = Path(ruta_archivo)
        
        if ruta.suffix not in EXTENSIONES_PERMITIDAS:
            return False
        
        for parte in ruta.parts:
            if parte in CARPETAS_EXCLUIR:
                return False
        
        if ruta.name.startswith('.') or ruta.name == '__init__.py':
            return False
        
        return True
    
    def escanear_proyecto(self):
        """Escanea todo el proyecto"""
        carpeta_raiz = self.encontrar_carpeta_raiz()
        print(f"\n📁 Escaneando desde: {carpeta_raiz}\n")
        
        for raiz, dirs, archivos in os.walk(carpeta_raiz):
            dirs[:] = [d for d in dirs if d not in CARPETAS_EXCLUIR and not d.startswith('.')]
            
            for archivo in archivos:
                ruta_completa = os.path.join(raiz, archivo)
                
                if self.deberia_procesar_archivo(ruta_completa):
                    registros = self.procesar_archivo(ruta_completa)
                    self.registros.extend(registros)
    
    def generar_csv(self):
        """Genera el archivo CSV con todos los campos"""
        os.makedirs(os.path.dirname(ARCHIVO_SALIDA_CSV), exist_ok=True)
        
        with open(ARCHIVO_SALIDA_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=CAMPOS_CSV)
            writer.writeheader()
            writer.writerows(self.registros)
        
        print(f"\n📊 CSV generado: {ARCHIVO_SALIDA_CSV}")
        print(f"   Total registros: {len(self.registros)}")
    
    def generar_json(self):
        """Genera el archivo JSON con estadísticas completas"""
        os.makedirs(os.path.dirname(ARCHIVO_SALIDA_JSON), exist_ok=True)
        
        # Convertir set a lista
        stats = self.estadisticas.copy()
        stats['tecnologias_detectadas'] = list(stats['tecnologias_detectadas'])
        
        datos_completos = {
            'estadisticas': stats,
            'registros': self.registros,
            'metadatos': {
                'fecha_analisis': datetime.now().isoformat(),
                'version_analyzer': '4.0.0',
                'ruta_proyecto': self.ruta_proyecto,
                'total_registros': len(self.registros)
            }
        }
        
        with open(ARCHIVO_SALIDA_JSON, 'w', encoding='utf-8') as f:
            json.dump(datos_completos, f, indent=2, ensure_ascii=False)
        
        print(f"📋 JSON generado: {ARCHIVO_SALIDA_JSON}")
    
    def mostrar_estadisticas(self):
        """Muestra estadísticas detalladas del análisis - VERSIÓN COMPLETA"""
        print("\n" + "="*80)
        print("📈 ESTADÍSTICAS COMPLETAS DEL ANÁLISIS")
        print("="*80)
        
        print(f"\n📁 Archivos:")
        print(f"   Total encontrados: {self.estadisticas['total_archivos']}")
        print(f"   Procesados: {self.estadisticas['archivos_procesados']}")
        print(f"   Con errores: {self.estadisticas['archivos_con_errores']}")
        
        print(f"\n🎯 Endpoints (PRIMERA PASADA):")
        print(f"   Total encontrados: {self.estadisticas['endpoints_encontrados']}")
        
        if self.estadisticas['endpoints_por_metodo']:
            print(f"\n   Por método HTTP:")
            for metodo, count in sorted(self.estadisticas['endpoints_por_metodo'].items()):
                print(f"      {metodo:7} : {count:3} endpoints")
        
        print(f"\n🏗️  Elementos de Código (SEGUNDA PASADA):")
        print(f"   Clases encontradas: {self.estadisticas['clases_encontradas']}")
        print(f"   Funciones encontradas: {self.estadisticas['funciones_encontradas']}")
        
        # Contar por categoría
        categorias = {}
        for registro in self.registros:
            cat = registro['categoria']
            categorias[cat] = categorias.get(cat, 0) + 1
        
        print(f"\n📊 Distribución por categoría:")
        for cat, count in sorted(categorias.items(), key=lambda x: x[1], reverse=True):
            print(f"   {cat:20} : {count:3} elementos")
        
        print(f"\n📂 Distribución por tipo de archivo:")
        for tipo, count in sorted(self.estadisticas['tipos_distribucion'].items()):
            print(f"   {tipo:15} : {count:3} archivos")
        
        if self.estadisticas['tecnologias_detectadas']:
            print(f"\n🔧 Tecnologías detectadas:")
            for tech in sorted(self.estadisticas['tecnologias_detectadas']):
                print(f"   • {tech}")
        
        print(f"\n🔀 Routers:")
        print(f"   Detectados: {self.estadisticas['routers_detectados']}")
        print(f"   Incluidos: {self.estadisticas['routers_incluidos']}")
        
        # Mostrar ejemplos de endpoints
        endpoints_encontrados = [r for r in self.registros if r['categoria'] == 'ENDPOINT']
        
        if endpoints_encontrados:
            print(f"\n🔍 Ejemplos de endpoints capturados:")
            print(f"   {'Método':<8} {'Endpoint':<45} {'Response Model':<25}")
            print(f"   {'-'*8} {'-'*45} {'-'*25}")
            
            for i, endpoint in enumerate(endpoints_encontrados[:10]):
                metodo = endpoint['metodo_http']
                ruta = endpoint['endpoint']
                modelo = endpoint['response_model'] or '-'
                
                if len(ruta) > 43:
                    ruta = ruta[:40] + '...'
                if len(modelo) > 23:
                    modelo = modelo[:20] + '...'
                
                print(f"   {metodo:<8} {ruta:<45} {modelo:<25}")
            
            if len(endpoints_encontrados) > 10:
                print(f"   ... y {len(endpoints_encontrados) - 10} endpoints más")
        
        # Mostrar ejemplos de clases
        clases_encontradas = [r for r in self.registros if r['categoria'] == 'CLASS']
        
        if clases_encontradas:
            print(f"\n🏗️  Ejemplos de clases encontradas:")
            print(f"   {'Nombre':<30} {'Tipo':<15} {'Archivo':<25}")
            print(f"   {'-'*30} {'-'*15} {'-'*25}")
            
            for i, clase in enumerate(clases_encontradas[:10]):
                nombre = clase['elemento']
                tipo_clase = clase['tipo']
                archivo = clase['nombre_archivo']
                
                if len(nombre) > 28:
                    nombre = nombre[:25] + '...'
                if len(archivo) > 23:
                    archivo = archivo[:20] + '...'
                
                print(f"   {nombre:<30} {tipo_clase:<15} {archivo:<25}")
            
            if len(clases_encontradas) > 10:
                print(f"   ... y {len(clases_encontradas) - 10} clases más")
        
        # Mostrar ejemplos de funciones
        funciones_encontradas = [r for r in self.registros if r['categoria'] == 'FUNCTION']
        
        if funciones_encontradas:
            print(f"\n⚡ Ejemplos de funciones encontradas:")
            print(f"   {'Nombre':<30} {'Tipo':<15} {'Async':<6}")
            print(f"   {'-'*30} {'-'*15} {'-'*6}")
            
            for i, funcion in enumerate(funciones_encontradas[:10]):
                nombre = funcion['elemento']
                tipo_func = funcion['tipo']
                es_async = '✓' if funcion['es_async'] else '-'
                
                if len(nombre) > 28:
                    nombre = nombre[:25] + '...'
                
                print(f"   {nombre:<30} {tipo_func:<15} {es_async:<6}")
            
            if len(funciones_encontradas) > 10:
                print(f"   ... y {len(funciones_encontradas) - 10} funciones más")
        
        print(f"\n📊 TOTAL DE REGISTROS GENERADOS: {len(self.registros)}")
        print("="*80)


def main():
    """Función principal"""
    print("="*80)
    print("🚀 ENHANCED CODE ANALYZER - Versión 4.0.0 COMPLETA")
    print("="*80)
    print("📋 DOBLE ANÁLISIS:")
    print("   1️⃣  PRIMERA PASADA: Endpoints (FastAPI, Flask, Django)")
    print("   2️⃣  SEGUNDA PASADA: Modelos, Schemas, Funciones, Configuraciones")
    print("="*80)
    print("\n🎯 Genera documentación completa para:")
    print("   • Agentes conversacionales (LLM embeddings)")
    print("   • Documentación técnica automática")
    print("   • Análisis de código y optimizaciones")
    print("   • Mapeo completo del proyecto")
    print("="*80)
    
    analyzer = EnhancedEndpointAnalyzer(RUTA_PROYECTO)
    
    print("\n🔍 Iniciando escaneo completo...")
    analyzer.escanear_proyecto()
    
    print("\n💾 Generando archivos de salida...")
    analyzer.generar_csv()
    analyzer.generar_json()
    
    analyzer.mostrar_estadisticas()
    
    print("\n" + "="*80)
    print("✅ ANÁLISIS COMPLETADO EXITOSAMENTE")
    print("="*80)
    print(f"\n📂 Archivos generados:")
    print(f"   • {ARCHIVO_SALIDA_CSV}")
    print(f"   • {ARCHIVO_SALIDA_JSON}")
    print(f"\n📊 Resumen:")
    print(f"   • Endpoints: {analyzer.estadisticas['endpoints_encontrados']}")
    print(f"   • Clases: {analyzer.estadisticas['clases_encontradas']}")
    print(f"   • Funciones: {analyzer.estadisticas['funciones_encontradas']}")
    print(f"   • Total registros: {len(analyzer.registros)}")
    print("="*80)
    print("\n💡 Próximos pasos:")
    print("   1. Usa el CSV para entrenar embeddings (RAG)")
    print("   2. Analiza el JSON para métricas de código")
    print("   3. Identifica oportunidades de refactorización")
    print("   4. Genera documentación automática")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()