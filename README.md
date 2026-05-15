# Content Suite API

Plataforma de **Brand Content Governance** impulsada por IA Generativa. Permite a las organizaciones definir su ADN de marca, generar contenido gobernado y auditarlo mediante un flujo de aprobación multimodal.

> **Reto Técnico** — Developer Gen AI Analyst 

Frontend: <https://reto-tecnico-alicorp-ia-gen.vercel.app/>

---

## Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Funcionalidades](#funcionalidades)
- [Tech Stack](#tech-stack)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Requisitos Previos](#requisitos-previos)
- [Instalación y Configuración](#instalación-y-configuración)
- [Ejecución](#ejecución)
- [API Endpoints](#api-endpoints)
- [Base de Datos](#base-de-datos)
- [Despliegue](#despliegue)
- [Roles del Sistema](#roles-del-sistema)

---

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend  │────▶│  FastAPI API │────▶│   Supabase   │
│   (Vercel)  │     │  (Cloud Run) │     │ (PostgreSQL) │
└─────────────┘     └──────┬───────┘     └──────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌────────┐  ┌────────┐  ┌────────┐
         │ OpenAI │  │  Groq  │  │ Langfuse│
         └────────┘  └────────┘  └────────┘
```

---

## Funcionalidades

### Módulo I — Brand DNA Architect
Genera manuales de identidad de marca estructurados y computables usando LLMs. Cada manual se almacena con embeddings vectoriales para búsqueda semántica (RAG).

### Módulo II — Content Generator
Produce copy de marketing que respeta estrictamente las reglas de marca mediante Retrieval-Augmented Generation (RAG).

### Módulo III — Content Governance
Flujo de aprobación en dos etapas:
1. **APPROVER_A** — Revisa y aprueba/rechaza el texto con feedback.
2. **APPROVER_B** — Auditoría visual multimodal de imágenes con modelos de visión para verificar cumplimiento de identidad visual.

---

## Tech Stack

| Categoría | Tecnología |
|---|---|
| **Framework** | FastAPI 0.115.8 |
| **Server** | Uvicorn 0.34.0 |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **LLMs** | OpenAI (GPT-4o-mini, GPT-4o), Groq (Llama3-70b) |
| **Embeddings** | OpenAI text-embedding-3-small (1536 dim) |
| **RAG** | LangChain ecosystem |
| **Observabilidad** | Langfuse |
| **Auth** | Supabase Auth + JWT |
| **Containerización** | Docker + Docker Compose |
| **Deploy** | Google Cloud Run |

---

## Estructura del Proyecto

```
Content-Suite-Backend/
├── app/
│   ├── main.py                 # Entry point FastAPI
│   └── config.py               # Configuración de variables de entorno
├── core/
│   ├── supabase_client.py      # Cliente Supabase
│   ├── openai_client.py        # Cliente OpenAI
│   ├── groq_client.py          # Cliente Groq
│   ├── google.py               # Modelo de visión
│   ├── langfuse_client.py      # Observabilidad
│   └── dependencies.py         # Inyección de dependencias
├── routes/
│   ├── auth_router.py          # /api/auth
│   ├── brand_dna_router.py     # /api (Brand DNA + RAG)
│   └── governance_router.py    # /api/gov
├── services/
│   ├── auth_service.py         # Login/registro
│   ├── llm.py                  # Generación de texto
│   ├── embedding.py            # Embeddings vectoriales
│   ├── rag_service.py          # Búsqueda semántica RAG
│   ├── governance_service.py   # CRUD de contenido
│   └── multimodal_audit.py     # Auditoría de imágenes
├── prompts/
│   └── prompts.py              # System prompts
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── deploy.ps1                  # Script despliegue completo
└── deploy-fast.ps1             # Script despliegue rápido
```

---

## Requisitos Previos

- Python 3.11+
- Docker y Docker Compose (opcional)
- Cuenta en **Supabase** con extensión `pgvector` habilitada
- API Keys de **OpenAI**, **Groq** y **Langfuse**
- Google Cloud SDK (`gcloud`) para despliegue en Cloud Run

---

## Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone <tu-repo-url>
cd Content-Suite-Backend
```

### 2. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Groq
GROQ_API_KEY=gsk_...

# Supabase
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-service-role-key

# Langfuse (observabilidad)
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

### 3. Configurar la base de datos

Ejecutar las sentencias SQL del archivo `sql-comands.mm.md` en el SQL Editor de Supabase para crear:
- Extensión `pgvector`
- Tablas: `profile_users`, `brand_dna`, `brand_dna_embeddings`, `content_items`
- Función RPC `match_brand_dna()`
- Índices vectoriales IVFFlat

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Ejecución

### Con Uvicorn directo

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Con Docker Compose

```bash
docker compose up --build
```

La API estará disponible en `http://localhost:8000`.

Documentación interactiva: `http://localhost:8000/docs`

---

## API Endpoints

### Health Check

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio |

### Autenticación (`/api/auth`)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/auth/login` | Autenticar usuario |
| `POST` | `/api/auth/register` | Registrar nuevo usuario |

### Brand DNA (`/api`)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/brand-dna` | Generar manual de marca con IA |
| `POST` | `/api/brand-dna/search` | Búsqueda semántica sobre embeddings |
| `POST` | `/api/rag/generate` | Generar contenido gobernado por Brand DNA |
| `GET` | `/api/brands` | Listar manuales de marca |

### Governance (`/api/gov`)

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/gov/content/create` | Crear contenido (estado: pending) |
| `GET` | `/api/gov/content/pending` | Listar contenido pendiente |
| `GET` | `/api/gov/content/approved` | Listar contenido aprobado |
| `GET` | `/api/gov/content/{id}` | Obtener contenido por ID |
| `GET` | `/api/gov/content` | Listar con filtros (marca, estado) |
| `POST` | `/api/gov/content/approve` | Aprobar/rechazar contenido (APPROVER_A) |
| `POST` | `/api/gov/content/audit-image` | Auditoría visual de imagen (APPROVER_B) |
| `POST` | `/api/gov/content/finalize-approval` | Finalizar aprobación post-auditoría |
| `GET` | `/api/gov/brands` | Listar marcas |
| `GET` | `/api/gov/selection/brands` | Marcas para dropdown UI |
| `GET` | `/api/gov/selection/content/{brand_id}` | Contenido para selección UI |

---

## Base de Datos

### Tablas principales

| Tabla | Propósito |
|---|---|
| `profile_users` | Perfiles de usuario vinculados a Supabase Auth |
| `brand_dna` | Manuales de identidad de marca generados por LLM |
| `brand_dna_embeddings` | Embeddings vectoriales (1536 dim) para RAG |
| `content_items` | Contenido generado con flujo de aprobación |

### Flujo de aprobación

```
CREATOR genera contenido
        │
        ▼
   status: pending
        │
        ▼
  APPROVER_A revisa texto
   ┌──────┴──────┐
   ▼             ▼
approved      rejected
   │
   ▼
APPROVER_B audita imagen
   ┌──────┴──────┐
   ▼             ▼
audit:passed  audit:failed
   │
   ▼
finalize_approval → approved
```

---

## Roles del Sistema

| Rol | Permisos |
|---|---|
| **CREATOR** | Generar contenido de marca |
| **APPROVER_A** | Aprobar/rechazar contenido textual con feedback |
| **APPROVER_B** | Auditoría visual de imágenes y aprobación final |
| **ADMIN** | Acceso completo a todas las funcionalidades |
