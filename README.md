# **Asistente Inteligente de Documentación para  `system api`**

- Objetivo: asistir en infromación sobre detalles ténicos de la demo y generar una documentación `README.md`.
- Usos en frameworks de python
- (Directo) Configurar entorno `venv_ia/`, api llm's en `.env` y Ejecutar directamente este comando `python -m ia.agent` en el directorio principal.
- (Opcional) Clonar el proyecto y directamente saltar a `Deploy Agente local`.


### **1 Deploy mediante Docker (Kernel-Linux 5.15) (modo contenedor)**
#### 1.1 renombrar el  `.env.docker` por `.env`
#### 1.2 Ejecución mediante Docker (modo contenedor)
```bash
# Construcción de imágenes
docker compose build

# Ejecución estándar
docker compose up -d

# Ejecución con perfil de desarrollo
docker compose --profile dev up -d
```

---
Validar acceso en:

> **Ruta: [http://localhost:8000/docs](http://localhost:8000/docs)**

### **2 Deploy Agente local**

```bash
# Crear entorno virtual
python -m venv venv_ia

# Activar entorno
.\venv_ia\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Debian

# Instalar dependencias
pip install -r requirements_ia.txt


# organizar scripts a csv
python -m ia.files_to_csv
# convertir embeddings
python -m ia.csv_to_embeddings
# deploy agente inteligente
python -m ia.agent

```
> **Ruta: [http://localhost:7865](http://localhost:7865)**