# **Despliegue del Proyecto: Sistema de Authenticación en Fastapi**

---
### **1 Deploy local (windows 10)**
#### **1.1 Requisitos del Sistema**

| Componente            | Versión recomendada   | Notas                    |
| --------------------- | --------------------- | ------------------------ |
| **Sistema Operativo** | Windows 10 / Debian   | Entornos compatibles     |
| **Python**            | 3.12.10               | Requerido                |
| **PostgreSQL**        | 17.6                  | Base de datos principal  |
| **Redis CLI**         | 5.0.14.1              | Módulo de caché opcional |
| **Docker**            | 29.0.0, build 3d4129b | Opcional                 |
| **Docker Compose**    | v2.40.3               | Opcional                 |

---

#### **1.2 Clonación y Configuración del Entorno**

```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Debian

# Instalar dependencias
pip install -r requirements.txt
```

---

#### **1.3 Configuración de la Base de Datos**

Ejecutar en **psql** o cualquier cliente SQL compatible:

```sql
CREATE DATABASE auth_db;
```

Verificar detalles de conexión mediante variables de entorno en el archivo `.env.local`.

---

#### **1.4 Ejecución del Proyecto (modo local)**

```bash
uvicorn app.main:app --reload
```

Acceso a la documentación interactiva:

> **Ruta:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### **2 Deploy mediante Docker (Kernel-Linux 5.15) (modo contenedor)**

#### 2.1 renombrar el  `.env.docker` por `.env`
#### 2.2 Ejecución mediante Docker (modo contenedor)
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
