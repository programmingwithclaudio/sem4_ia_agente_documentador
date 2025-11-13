#!/usr/bin/env python3
"""
Sistema de Embeddings V3 - VERSIÓN CORREGIDA
Salidas:
- Detecta automáticamente campos vacíos vs llenos
- Genera texto de búsqueda MÁS RICO con TODOS los datos disponibles
- Maneja correctamente endpoint_completo vacío
- Incluye información de routers, decoradores, includes
- Texto de búsqueda más descriptivo para el agente
"""
import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import StandardScaler
import faiss
import redis
import json
import logging
from typing import List, Dict, Tuple


class ConfigEmbeddingsV3:
    """Configuración unificada"""
    BASE_PATH = Path("datasets")
    INPUT_CSV = BASE_PATH / "documentacion.csv"
    OUTPUT_PATH = BASE_PATH / "embeddings"
    
    MODEL_NAME = 'sentence-transformers/all-MiniLM-L6-v2'
    EMBEDDING_DIM = 384
    
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 3
    
    @classmethod
    def setup(cls):
        cls.OUTPUT_PATH.mkdir(exist_ok=True, parents=True)


class GeneradorTextoBusquedaV3Fixed:
    """
    Genera texto
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def _limpiar_texto(self, texto):
        if pd.isna(texto) or texto is None or texto == '':
            return ""
        return str(texto).strip()
    
    def _get_safe(self, row: pd.Series, key: str, default: str = "") -> str:
        """Obtiene valor de forma segura"""
        try:
            val = row.get(key, default)
            return self._limpiar_texto(val)
        except:
            return default
    
    def _extraer_routers_desde_json(self, include_routers_str: str) -> List[str]:
        """
        Extrae información de routers desde el JSON de include_routers
        """
        if not include_routers_str:
            return []
        
        try:
            routers_list = json.loads(include_routers_str)
            info = []
            for router in routers_list:
                if isinstance(router, dict):
                    router_name = router.get('router', '')
                    prefix = router.get('prefix', '')
                    tags = router.get('tags', '')
                    
                    if router_name or prefix:
                        parte = []
                        if router_name:
                            parte.append(f"router {router_name}")
                        if prefix:
                            parte.append(f"prefix {prefix}")
                        if tags:
                            parte.append(f"tags {tags}")
                        
                        info.append(' '.join(parte))
            
            return info
        except:
            return []
    
    def generar_para_route(self, row: pd.Series) -> str:
        """
        Texto para endpoints
        """
        partes = []
        
        # 1. ENDPOINT (prioridad: endpoint_completo > endpoint)
        endpoint_completo = self._get_safe(row, 'endpoint_completo')
        endpoint_base = self._get_safe(row, 'endpoint')
        metodo = self._get_safe(row, 'metodo_http') or 'HTTP'
        
        # ✅ MEJORA: Si endpoint_completo está vacío, construir desde endpoint_base + router_prefix
        if endpoint_completo:
            partes.append(f"endpoint {metodo} {endpoint_completo}")
        elif endpoint_base:
            # Intentar construir ruta completa
            router_prefix = self._get_safe(row, 'router_prefix')
            if router_prefix and router_prefix.startswith('/'):
                ruta_completa = f"{router_prefix}{endpoint_base}".replace('//', '/')
                partes.append(f"endpoint {metodo} {ruta_completa}")
            else:
                partes.append(f"endpoint {metodo} {endpoint_base}")
        
        # 2. INFORMACIÓN DE ROUTER
        router_padre = self._get_safe(row, 'router_padre')
        if router_padre:
            partes.append(f"router {router_padre}")
        
        # 3. DESCRIPCIONES (todas las disponibles)
        for col in ['descripcion', 'summary', 'description']:
            texto = self._get_safe(row, col)
            if texto:
                partes.append(texto)
        
        # 4. FUNCIÓN Y ARCHIVO
        elemento = self._get_safe(row, 'elemento')
        ruta = self._get_safe(row, 'ruta')
        
        if elemento:
            partes.append(f"función {elemento}")
        if ruta:
            partes.append(f"archivo {ruta}")
        
        # 5. CATEGORÍA Y TAGS
        categoria = self._get_safe(row, 'categoria')
        if categoria:
            partes.append(f"categoría {categoria}")
        
        tags = self._get_safe(row, 'tags')
        if tags:
            partes.append(f"tags {tags}")
        
        # 6. INFORMACIÓN DE INCLUDE_ROUTERS (si es main.py)
        include_routers = self._get_safe(row, 'include_routers')
        if include_routers:
            routers_info = self._extraer_routers_desde_json(include_routers)
            if routers_info:
                partes.append(f"incluye {' '.join(routers_info)}")
        
        # 7. PARÁMETROS (todos)
        parametros_info = []
        for col in ['parametros', 'parametros_query', 'parametros_path', 'parametros_body']:
            texto = self._get_safe(row, col)
            if texto:
                parametros_info.append(texto)
        
        if parametros_info:
            partes.append(f"parámetros {' '.join(parametros_info)}")
        
        # 8. RESPONSE MODEL
        response_model = self._get_safe(row, 'response_model')
        if response_model:
            partes.append(f"responde {response_model}")
        
        # 9. STATUS CODE
        status_code = self._get_safe(row, 'status_code')
        if status_code:
            partes.append(f"status {status_code}")
        
        # 10. TECNOLOGÍAS
        tecnologias = self._get_safe(row, 'tecnologias')
        if tecnologias:
            partes.append(f"usa {tecnologias}")
        
        # 11. ASYNC
        es_async = self._get_safe(row, 'es_async')
        if es_async in ['True', 'true', '1', True]:
            partes.append("asíncrono")
        
        # 12. DECORADORES (si tiene)
        decoradores = self._get_safe(row, 'decoradores')
        if decoradores and decoradores not in ['[]', '']:
            partes.append(f"decoradores {decoradores}")
        
        # 13. CÓDIGO (primera línea)
        codigo_limpio = self._get_safe(row, 'codigo_limpio')
        if codigo_limpio:
            primera_linea = codigo_limpio.split('\n')[0]
            partes.append(primera_linea[:100])
        
        return ' '.join(partes)
    
    def generar_para_model(self, row: pd.Series) -> str:
        """Mantiene lógica original"""
        partes = [
            f"modelo {self._get_safe(row, 'elemento')}",
            f"tabla base de datos",
            self._get_safe(row, 'descripcion'),
            f"archivo {self._get_safe(row, 'ruta')}"
        ]
        
        if self._get_safe(row, 'categoria'):
            partes.append(f"categoría {row['categoria']}")
        
        if self._get_safe(row, 'codigo_limpio'):
            lineas = [l.strip() for l in row['codigo_limpio'].split('\n') 
                     if any(keyword in l.lower() for keyword in ['=', ':', 'column', 'relationship'])]
            partes.extend(lineas[:8])
        
        return ' '.join(partes)
    
    def generar_para_schema(self, row: pd.Series) -> str:
        """Mantiene lógica original"""
        partes = [
            f"schema {self._get_safe(row, 'elemento')}",
            f"validación pydantic",
            self._get_safe(row, 'descripcion'),
            f"archivo {self._get_safe(row, 'ruta')}"
        ]
        
        if self._get_safe(row, 'response_model'):
            partes.append(f"usado como response_model {row['response_model']}")
        
        if self._get_safe(row, 'codigo_limpio'):
            lineas = [l.strip() for l in row['codigo_limpio'].split('\n') 
                     if ':' in l and '=' not in l]
            partes.extend(lineas[:8])
        
        return ' '.join(partes)
    
    def generar_para_config(self, row: pd.Series) -> str:
        """Mantiene lógica original"""
        partes = [
            f"configuración {self._get_safe(row, 'elemento')}",
            self._get_safe(row, 'descripcion'),
            f"archivo {self._get_safe(row, 'ruta')}"
        ]
        
        if self._get_safe(row, 'tecnologias'):
            partes.append(f"tecnologías {row['tecnologias']}")
        
        return ' '.join(partes)
    
    def generar(self, row: pd.Series) -> str:
        """
        Mejor detección de tipos
        """
        tipo = self._get_safe(row, 'tipo')
        
        # Detectar endpoint por múltiples señales
        tiene_endpoint = (
            self._get_safe(row, 'endpoint') or 
            self._get_safe(row, 'endpoint_completo') or
            self._get_safe(row, 'metodo_http') or
            'endpoint' in str(row.get('endpoint', '')).lower()
        )
        
        if tipo == 'route' or tiene_endpoint:
            return self.generar_para_route(row)
        elif tipo == 'model':
            return self.generar_para_model(row)
        elif tipo == 'schema':
            return self.generar_para_schema(row)
        elif tipo in ['config', 'auth', 'util']:
            return self.generar_para_config(row)
        else:
            # Fallback: intentar como route
            return self.generar_para_route(row)


class GeneradorEmbeddingsV3:
    """Pipeline con generador mejorado"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.model = SentenceTransformer(ConfigEmbeddingsV3.MODEL_NAME)
        self.model.max_seq_length = 512
        self.generador_texto = GeneradorTextoBusquedaV3Fixed()
        self.scaler = StandardScaler()
    
    def _setup_logger(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - [%(levelname)s] %(message)s'
        )
        return logging.getLogger(__name__)
    
    def leer_csv(self) -> pd.DataFrame:
        """Lee CSV y analiza estructura"""
        csv_path = ConfigEmbeddingsV3.INPUT_CSV
        
        if not csv_path.exists():
            raise FileNotFoundError(f"No se encontró: {csv_path}")
        
        self.logger.info(f"Leyendo CSV: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            self.logger.info(f"✅ CSV: {len(df)} registros, {len(df.columns)} columnas")
            
      
            self.logger.info("\n📊 ANÁLISIS DE CAMPOS:")
            
            campos_importantes = [
                'endpoint', 'endpoint_completo', 'router_padre', 'router_prefix',
                'include_routers', 'metodo_http', 'descripcion'
            ]
            
            for campo in campos_importantes:
                if campo in df.columns:
                    no_vacios = df[campo].notna() & (df[campo] != '') & (df[campo] != '[]')
                    count = no_vacios.sum()
                    porcentaje = (count / len(df)) * 100
                    
                    if count > 0:
                        self.logger.info(f"   ✅ {campo:20} → {count:3} registros ({porcentaje:.1f}%)")
                    else:
                        self.logger.info(f"   ⚠️  {campo:20} → VACÍO")
            
            df = df.fillna('')
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Error: {e}")
            raise
    
    def generar_texto_busqueda(self, df: pd.DataFrame) -> pd.DataFrame:
        """Genera texto de búsqueda mejorado"""
        self.logger.info("\n🔍 Generando texto de búsqueda MEJORADO...")
        
        df['texto_busqueda'] = df.apply(self.generador_texto.generar, axis=1)
        
        longitudes = df['texto_busqueda'].str.len()
        self.logger.info(f"📏 Longitud - Avg: {longitudes.mean():.1f}, "
                        f"Min: {longitudes.min()}, Max: {longitudes.max()}")
        

        self.logger.info("\n📝 EJEMPLOS DE TEXTO GENERADO:")
        for idx in range(min(5, len(df))):
            self.logger.info(f"\n[{idx+1}] {df.iloc[idx]['tipo']} | {df.iloc[idx]['elemento']}")
            self.logger.info(f"    Longitud: {len(df.iloc[idx]['texto_busqueda'])} chars")
            self.logger.info(f"    Texto: {df.iloc[idx]['texto_busqueda'][:250]}...")
        
        return df
    
    def extraer_features(self, df: pd.DataFrame) -> np.ndarray:
        """Features (8 dims)"""
        features = []
        
        tipo_weight = {
            'route': 5.0,
            'router': 4.5,
            'model': 4.0,
            'schema': 3.0,
            'auth': 2.0,
            'config': 1.5,
            'util': 1.0
        }
        
        tiene_columna_router_prefix = 'router_prefix' in df.columns
        
        for _, row in df.iterrows():
            num_parametros = 0
            for col in ['parametros', 'parametros_query', 'parametros_path', 'parametros_body']:
                if col in row and row[col]:
                    num_parametros += len(str(row[col]).split(','))
            
            tiene_router_prefix = 0.0
            if tiene_columna_router_prefix:
                tiene_router_prefix = 1.0 if row.get('router_prefix', '') else 0.0
            
            feature_vector = [
                tipo_weight.get(row.get('tipo', ''), 0.5),
                1.0 if row.get('endpoint', '') or row.get('endpoint_completo', '') else 0.0,
                min(len(str(row.get('codigo_limpio', '')).split('\n')), 100),
                1.0 if row.get('dependencias', '') else 0.0,
                min(num_parametros, 10),
                1.0 if row.get('es_async', False) in ['True', 'true', '1', True] else 0.0,
                1.0 if row.get('response_model', '') else 0.0,
                tiene_router_prefix
            ]
            
            features.append(feature_vector)
        
        features = np.array(features, dtype='float32')
        
        if len(features) > 0:
            features = self.scaler.fit_transform(features)
        
        self.logger.info(f"🔢 Features: {features.shape[1]} dims")
        
        return features
    
    def generar_embeddings(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Genera embeddings completos"""
        self.logger.info(f"\n🧮 Generando embeddings para {len(df)} registros...")
        
        textos = df['texto_busqueda'].tolist()
        embeddings_texto = self.model.encode(
            textos,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True
        )
        
        features = self.extraer_features(df)
        
        embeddings_final = np.hstack([
            embeddings_texto,
            features
        ]).astype('float32')
        
        norms = np.linalg.norm(embeddings_final, axis=1, keepdims=True)
        embeddings_final = embeddings_final / norms
        
        self.logger.info(f"✅ Embeddings:")
        self.logger.info(f"   - Texto: {embeddings_texto.shape[1]}")
        self.logger.info(f"   - Features: {features.shape[1]}")
        self.logger.info(f"   - Total: {embeddings_final.shape[1]}")
        
        return embeddings_final, embeddings_texto
    
    def crear_indice_faiss(self, embeddings: np.ndarray):
        """Crea índice FAISS"""
        dimension = embeddings.shape[1]
        
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        
        self.logger.info(f"✅ FAISS: {index.ntotal} vectores, {dimension} dims")
        
        output_file = ConfigEmbeddingsV3.OUTPUT_PATH / "documentacion.index"
        faiss.write_index(index, str(output_file))
        
        np.save(ConfigEmbeddingsV3.OUTPUT_PATH / "embeddings.npy", embeddings)
        
        return index
    
    def indexar_redis(self, df: pd.DataFrame):
        """
        Indexa TODOS los campos disponibles
        """
        self.logger.info("\n💾 Indexando en Redis...")
        
        try:
            redis_client = redis.Redis(
                host=ConfigEmbeddingsV3.REDIS_HOST,
                port=ConfigEmbeddingsV3.REDIS_PORT,
                db=ConfigEmbeddingsV3.REDIS_DB,
                decode_responses=True
            )
            
            redis_client.flushdb()
            pipe = redis_client.pipeline()
            
            for idx, row in df.iterrows():
                chunk_key = f"chunk:{idx}"
                
                # CAMPOS DISPONIBLES
                metadata = {
                    'id': str(idx),
                    'tipo': str(row.get('tipo', '')),
                    'archivo': str(row.get('nombre_archivo', '')),
                    'ruta': str(row.get('ruta', '')),
                    'elemento': str(row.get('elemento', '')),
                    'categoria': str(row.get('categoria', '')),
                    'endpoint': str(row.get('endpoint', '')),
                    'endpoint_completo': str(row.get('endpoint_completo', '')),
                    'metodo_http': str(row.get('metodo_http', '')),
                    'descripcion': str(row.get('descripcion', '')),
                    'summary': str(row.get('summary', '')),
                    'description': str(row.get('description', '')),
                    'tags': str(row.get('tags', '')),
                    'response_model': str(row.get('response_model', '')),
                    'status_code': str(row.get('status_code', '')),
                    'contenido': str(row.get('codigo_limpio', ''))[:2000],
                    'codigo_limpio': str(row.get('codigo_limpio', ''))[:2000],
                    'dependencias': str(row.get('dependencias', '')),
                    'tecnologias': str(row.get('tecnologias', '')),
                    'funciones': json.dumps([row.get('elemento', '')]),
                    'complejidad': str(len(str(row.get('codigo_limpio', '')).split('\n'))),
                    'router_padre': str(row.get('router_padre', '')),
                    'router_prefix': str(row.get('router_prefix', '')),
                    'include_routers': str(row.get('include_routers', '')),
                    'decoradores': str(row.get('decoradores', '')),
                    'es_async': str(row.get('es_async', '')),
                    'texto_busqueda': str(row.get('texto_busqueda', ''))[:1000]  # ✅ NUEVO
                }
                
                pipe.hmset(chunk_key, metadata)
                
                # Índices secundarios
                if row.get('endpoint', '') or row.get('endpoint_completo', ''):
                    endpoint = row.get('endpoint_completo', '') or row.get('endpoint', '')
                    pipe.sadd(f"endpoint:{row.get('metodo_http', 'ANY')}:{endpoint}", idx)
                
                if row.get('router_padre', ''):
                    pipe.sadd(f"router:{row['router_padre']}", idx)
                
                pipe.sadd(f"tipo:{row.get('tipo', '')}", idx)
                pipe.sadd(f"archivo:{row.get('nombre_archivo', '')}", idx)
            
            pipe.execute()
            
            self.logger.info(f"✅ {len(df)} registros en Redis DB{ConfigEmbeddingsV3.REDIS_DB}")
            
        except Exception as e:
            self.logger.error(f"❌ Error Redis: {e}")
            raise
    
    def crear_mapeo_indices(self, df: pd.DataFrame):
        """Crea mapeo con TODOS los campos"""
        self.logger.info("\n📋 Creando mapeo de índices...")
        
        mapeo = {}
        for idx, row in df.iterrows():
            entrada = {
                'id': int(idx),
                'archivo': str(row.get('nombre_archivo', '')),
                'tipo': str(row.get('tipo', '')),
                'elemento': str(row.get('elemento', '')),
                'endpoint': str(row.get('endpoint', '')),
                'endpoint_completo': str(row.get('endpoint_completo', '')),
                'router_padre': str(row.get('router_padre', '')),
                'categoria': str(row.get('categoria', '')),
                'descripcion': str(row.get('descripcion', ''))[:200]
            }
            
            mapeo[str(idx)] = entrada
        
        output_file = ConfigEmbeddingsV3.OUTPUT_PATH / "mapeo_indices.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(mapeo, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Mapeo guardado: {output_file}")
        
        return mapeo


def ejecutar_pipeline_v3():
    """Pipeline completo"""
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("🚀 PIPELINE V3 - VERSIÓN CORREGIDA")
    logger.info("=" * 80)
    
    ConfigEmbeddingsV3.setup()
    
    generador = GeneradorEmbeddingsV3()
    
    try:
        df = generador.leer_csv()
        df = generador.generar_texto_busqueda(df)
        embeddings, embeddings_texto = generador.generar_embeddings(df)
        index = generador.crear_indice_faiss(embeddings)
        generador.indexar_redis(df)
        mapeo = generador.crear_mapeo_indices(df)
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ PIPELINE COMPLETADO")
        logger.info("=" * 80)
        logger.info(f"📊 Registros: {len(df)}")
        logger.info(f"🔢 Dimensión: {embeddings.shape[1]}")
        
        return index, df, mapeo
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    index, df, mapeo = ejecutar_pipeline_v3()
    
    print("\n" + "=" * 80)
    print("🔍 VALIDACIÓN")
    print("=" * 80)
    
    # Mostrar ejemplos de texto de búsqueda
    print("\n📝 EJEMPLOS DE TEXTO DE BÚSQUEDA GENERADO:")
    for idx in range(min(3, len(df))):
        print(f"\n[{idx}] {df.iloc[idx]['tipo']} | {df.iloc[idx]['elemento']}")
        print(f"Longitud: {len(df.iloc[idx]['texto_busqueda'])} caracteres")
        print(f"Texto:\n{df.iloc[idx]['texto_busqueda']}\n")
        print("-" * 80)