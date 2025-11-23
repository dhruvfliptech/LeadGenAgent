# n8n Architecture - CraigLeads Pro

Visual architecture diagrams and technical specifications for n8n integration.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CraigLeads Pro System                        │
│                                                                       │
│  ┌──────────────────┐         ┌─────────────┐       ┌─────────────┐│
│  │   Frontend UI    │◄────────┤   Backend   ├──────►│  Database   ││
│  │   React/Vite     │  HTTP   │   FastAPI   │       │ PostgreSQL  ││
│  │   Port: 3000     │         │ Port: 8000  │       │             ││
│  └──────────────────┘         └──────┬──────┘       └─────────────┘│
│                                       │                              │
│                                       │ HTTP                         │
│                                       │ Webhooks                     │
│                                       │                              │
└───────────────────────────────────────┼──────────────────────────────┘
                                        │
                                        ↓
┌───────────────────────────────────────────────────────────────────────┐
│                        n8n Workflow Engine                             │
│                        Port: 5678                                      │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │                      Workflow Orchestration                       ││
│  │                                                                   ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ ││
│  │  │ Lead Processing │  │ Demo Generation │  │ Video Creation  │ ││
│  │  │   Workflow      │  │    Workflow     │  │    Workflow     │ ││
│  │  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘ ││
│  │           │                    │                     │          ││
│  │           └────────────────────┼─────────────────────┘          ││
│  │                               │                                 ││
│  └───────────────────────────────┼─────────────────────────────────┘│
│                                   │                                  │
│  ┌──────────────────────────────┼─────────────────────────────────┐│
│  │         Custom Nodes          │                                 ││
│  │                               │                                 ││
│  │  ┌────────────────────────────▼───────────────────────────────┐││
│  │  │           CraigLeads Pro API Node                          │││
│  │  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │││
│  │  │  │   Lead   │ │DemoSite  │ │  Video   │ │  Email   │     │││
│  │  │  │Resource  │ │Resource  │ │Resource  │ │Resource  │     │││
│  │  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │││
│  │  └────────────────────────────────────────────────────────────┘││
│  └──────────────────────────────────────────────────────────────────┘│
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐│
│  │                      Data Persistence                             ││
│  │                                                                   ││
│  │  ┌──────────────────┐         ┌──────────────────┐              ││
│  │  │   PostgreSQL     │         │      Redis       │              ││
│  │  │   Database       │         │   Queue/Cache    │              ││
│  │  │                  │         │                  │              ││
│  │  │ • Workflows      │         │ • Job Queue      │              ││
│  │  │ • Executions     │         │ • Cache          │              ││
│  │  │ • Credentials    │         │ • Sessions       │              ││
│  │  └──────────────────┘         └──────────────────┘              ││
│  └──────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Lead Generation Pipeline                      │
└─────────────────────────────────────────────────────────────────────┘

1. LEAD SCRAPED
   ─────────────
   Backend Scraper
        │
        ├─ Store in Database
        │
        └─ Trigger Webhook ──────────┐
                                      │
                                      ↓
                         ┌────────────────────────┐
                         │ n8n: Lead Processing   │
                         │   Workflow             │
                         └────────────────────────┘
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                         ↓            ↓            ↓
                    Score Lead   Extract Data   Validate
                         │            │            │
                         └────────────┼────────────┘
                                      │
                         ┌────────────┴────────────┐
                         │   Approval Decision     │
                         └─────────────────────────┘
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                High Score│       Medium│       Low │
                (>85)     │       (60-85)│      (<60)│
                         │            │            │
                         ↓            ↓            ↓
                   Auto-Approve  Human Review   Reject
                         │            │            │
                         └────────────┼────────────┘
                                      │
                                 [Approved]
                                      │
                                      ↓

2. DEMO GENERATION
   ─────────────────
                         ┌────────────────────────┐
                         │ n8n: Demo Generation   │
                         │   Workflow             │
                         └────────────────────────┘
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                         ↓            ↓            ↓
                  Get Lead Data  Call API    Wait Deploy
                         │            │            │
                         └────────────┼────────────┘
                                      │
                         ┌────────────────────────┐
                         │   Demo Site Created    │
                         │   URL: demo.site.com   │
                         └────────────────────────┘
                                      │
                         Update Lead ─┤
                         Set demo_url │
                                      ↓

3. VIDEO CREATION
   ────────────────
                         ┌────────────────────────┐
                         │ n8n: Video Creation    │
                         │   Workflow             │
                         └────────────────────────┘
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                         ↓            ↓            ↓
                  Generate Script  Create Video  Render
                         │            │            │
                         └────────────┼────────────┘
                                      │
                         ┌────────────────────────┐
                         │   Video Generated      │
                         │   URL: video.mp4       │
                         └────────────────────────┘
                                      │
                         Update Lead ─┤
                         Set video_url│
                                      ↓

4. EMAIL OUTREACH
   ────────────────
                         ┌────────────────────────┐
                         │ n8n: Email Outreach    │
                         │   Workflow             │
                         └────────────────────────┘
                                      │
                         ┌────────────┼────────────┐
                         │            │            │
                         ↓            ↓            ↓
                  Get Contact    Build Email   Send Email
                         │            │            │
                         └────────────┼────────────┘
                                      │
                         ┌────────────────────────┐
                         │   Email Sent           │
                         │   Status: delivered    │
                         └────────────────────────┘
                                      │
                         Update Lead ─┤
                         Set contacted│
                                      ↓
                                   SUCCESS!
```

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         n8n Components                               │
└─────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                          Frontend Layer                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    n8n Web UI (Vue.js)                        │ │
│  │  • Workflow Editor                                            │ │
│  │  • Node Configuration                                         │ │
│  │  • Execution Viewer                                           │ │
│  │  • Credential Manager                                         │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                               ↕                                     │
│                           Port 5678                                 │
└────────────────────────────────────────────────────────────────────┘
                                 ↕
┌────────────────────────────────────────────────────────────────────┐
│                       Application Layer                             │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────┐         ┌─────────────────────┐          │
│  │   Workflow Engine   │         │   Execution Engine  │          │
│  │  • Parse workflow   │         │  • Run nodes        │          │
│  │  • Validate         │         │  • Handle data      │          │
│  │  • Orchestrate      │         │  • Error handling   │          │
│  └─────────────────────┘         └─────────────────────┘          │
│                                                                     │
│  ┌─────────────────────┐         ┌─────────────────────┐          │
│  │   Webhook Manager   │         │   Credential Store  │          │
│  │  • Register hooks   │         │  • Encrypt creds    │          │
│  │  • Route requests   │         │  • Validate auth    │          │
│  │  • Handle response  │         │  • Test connection  │          │
│  └─────────────────────┘         └─────────────────────┘          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Custom Nodes                               │ │
│  │  ┌────────────────────────────────────────────────────────┐  │ │
│  │  │           CraigLeads Pro Node                          │  │ │
│  │  │  • Lead Resource      (Get, Update, Status)           │  │ │
│  │  │  • Demo Site Resource (Create, Get, Deploy)           │  │ │
│  │  │  • Video Resource     (Create, Get, Status)           │  │ │
│  │  │  • Email Resource     (Send)                          │  │ │
│  │  │  • Analytics Resource (Overview, Conversions)         │  │ │
│  │  └────────────────────────────────────────────────────────┘  │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                                 ↕
┌────────────────────────────────────────────────────────────────────┐
│                         Queue Layer                                 │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                        Redis Queue                            │ │
│  │  • Job Queue         (Bull)                                   │ │
│  │  • Cache Layer       (Session, temp data)                     │ │
│  │  • Pub/Sub           (Real-time updates)                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
                                 ↕
┌────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                  │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                   PostgreSQL Database                         │ │
│  │                                                               │ │
│  │  Tables:                                                      │ │
│  │  ├─ workflow_entity        (Workflow definitions)            │ │
│  │  ├─ execution_entity       (Execution history)               │ │
│  │  ├─ credentials_entity     (Encrypted credentials)           │ │
│  │  ├─ webhook_entity         (Webhook registrations)           │ │
│  │  ├─ n8n_workflows          (Custom: workflow metadata)       │ │
│  │  ├─ n8n_executions         (Custom: execution tracking)      │ │
│  │  └─ n8n_webhook_logs       (Custom: webhook activity)        │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
```

---

## Network Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Network                               │
│                      Network: n8n_network                            │
│                      Subnet: 172.25.0.0/16                           │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐         ┌──────────────────────┐
│       Host OS        │         │   External Network   │
│    (localhost)       │         │    (Internet)        │
└──────────────────────┘         └──────────────────────┘
         │                                  │
         │ Port Mapping                     │ Outbound
         │ 5678:5678                        │ HTTPS/HTTP
         │                                  │
         ↓                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Bridge                                │
│                      n8n_network (bridge)                            │
│                                                                      │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐   │
│  │      n8n       │    │   PostgreSQL   │    │     Redis      │   │
│  │   Container    │◄───┤   Container    │    │   Container    │   │
│  │                │    │                │    │                │   │
│  │  Port: 5678    │    │  Port: 5432    │    │  Port: 6379    │   │
│  │  (exposed)     │    │  (internal)    │    │  (internal)    │   │
│  └────────────────┘    └────────────────┘    └────────────────┘   │
│         │                       │                      │            │
│         └───────────────────────┴──────────────────────┘            │
│                          Internal DNS                               │
│                     postgres:5432, redis:6379                       │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ Docker host.docker.internal
         │ (Access host services from container)
         │
         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         Host Services                                │
│                                                                      │
│  ┌────────────────┐              ┌────────────────┐                │
│  │    Backend     │              │    Frontend    │                │
│  │    FastAPI     │              │   React/Vite   │                │
│  │  Port: 8000    │              │   Port: 3000   │                │
│  └────────────────┘              └────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Webhook Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Webhook Communication                           │
└─────────────────────────────────────────────────────────────────────┘

Direction 1: Backend → n8n
───────────────────────────

Backend Event
     │
     ↓
┌─────────────────────────────────┐
│  Backend Webhook Trigger        │
│  /api/v1/n8n-webhooks/...       │
└─────────────────────────────────┘
     │
     │ HTTP POST
     │ JSON Payload
     │
     ↓
┌─────────────────────────────────┐
│  n8n Webhook Node               │
│  Listening at:                  │
│  http://localhost:5678/webhook/ │
└─────────────────────────────────┘
     │
     ↓
┌─────────────────────────────────┐
│  n8n Workflow Execution         │
│  Process, Transform, Act        │
└─────────────────────────────────┘


Direction 2: n8n → Backend
───────────────────────────

n8n Workflow Node
     │
     ↓
┌─────────────────────────────────┐
│  CraigLeads Pro API Node        │
│  Configure operation            │
└─────────────────────────────────┘
     │
     │ HTTP Request
     │ Authorization: Bearer <API_KEY>
     │
     ↓
┌─────────────────────────────────┐
│  Backend API Endpoint           │
│  http://host.docker.internal:   │
│       8000/api/v1/...           │
└─────────────────────────────────┘
     │
     ↓
┌─────────────────────────────────┐
│  Backend Processing             │
│  Database, Logic, Response      │
└─────────────────────────────────┘
     │
     │ JSON Response
     │
     ↓
┌─────────────────────────────────┐
│  n8n Receives Data              │
│  Continue workflow              │
└─────────────────────────────────┘
```

---

## Execution Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Workflow Execution Flow                         │
└─────────────────────────────────────────────────────────────────────┘

Workflow Trigger (Webhook/Schedule/Manual)
            │
            ↓
┌──────────────────────────────────────┐
│  1. Initialize Execution             │
│     • Create execution ID            │
│     • Log start time                 │
│     • Set status: "running"          │
└──────────────────────────────────────┘
            │
            ↓
┌──────────────────────────────────────┐
│  2. Load Workflow                    │
│     • Parse workflow JSON            │
│     • Validate nodes                 │
│     • Load credentials               │
└──────────────────────────────────────┘
            │
            ↓
┌──────────────────────────────────────┐
│  3. Execute Nodes (Sequential)       │
│                                      │
│     Node 1: Webhook                  │
│        │                             │
│        ↓                             │
│     Node 2: CraigLeads Pro API       │
│        │                             │
│        ↓                             │
│     Node 3: Conditional Logic        │
│        ├─ True Branch               │
│        └─ False Branch              │
│           │                          │
│           ↓                          │
│     Node 4: Update Status            │
│        │                             │
│        ↓                             │
│     Node 5: Send Notification        │
└──────────────────────────────────────┘
            │
            ↓
┌──────────────────────────────────────┐
│  4. Handle Results                   │
│     • Success: Log output            │
│     • Error: Log error, retry?       │
└──────────────────────────────────────┘
            │
            ↓
┌──────────────────────────────────────┐
│  5. Save Execution                   │
│     • Store in database              │
│     • Update statistics              │
│     • Set status: "success"/"error"  │
│     • Calculate duration             │
└──────────────────────────────────────┘
            │
            ↓
┌──────────────────────────────────────┐
│  6. Cleanup                          │
│     • Release resources              │
│     • Clear temp data                │
│     • Send webhooks (if configured)  │
└──────────────────────────────────────┘
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Security Layers                              │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                        Layer 1: Network Security                      │
├──────────────────────────────────────────────────────────────────────┤
│  • Docker isolated network (172.25.0.0/16)                           │
│  • Only port 5678 exposed to host                                    │
│  • Internal services (PostgreSQL, Redis) not accessible from host    │
│  • Use host.docker.internal for accessing host services              │
└──────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────┐
│                     Layer 2: Application Security                     │
├──────────────────────────────────────────────────────────────────────┤
│  • Basic Auth for UI access (username/password)                      │
│  • API Key authentication for programmatic access                    │
│  • JWT tokens for API sessions                                       │
│  • CORS configuration                                                 │
│  • Rate limiting (configurable)                                       │
└──────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────┐
│                      Layer 3: Data Security                           │
├──────────────────────────────────────────────────────────────────────┤
│  • Credentials encrypted at rest (AES-256)                           │
│  • Encryption key (N8N_ENCRYPTION_KEY)                               │
│  • Database SSL connections (optional)                                │
│  • Secure password storage (bcrypt)                                   │
└──────────────────────────────────────────────────────────────────────┘
                                  ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    Layer 4: Execution Security                        │
├──────────────────────────────────────────────────────────────────────┤
│  • Sandboxed JavaScript execution (VM2)                              │
│  • Input validation                                                   │
│  • Output sanitization                                                │
│  • Resource limits (memory, CPU)                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Scaling Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Horizontal Scaling Strategy                       │
└─────────────────────────────────────────────────────────────────────┘

Current Setup (Single Instance)
────────────────────────────────
┌──────────────┐
│     n8n      │
│  (Main + UI) │
└──────────────┘
       │
       ↓
┌──────────────┐
│  PostgreSQL  │
│    Redis     │
└──────────────┘


Scaled Setup (Queue Mode)
──────────────────────────
                ┌──────────────┐
                │  Load        │
                │  Balancer    │
                └──────┬───────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ↓              ↓              ↓
┌──────────────┐┌──────────────┐┌──────────────┐
│     n8n      ││     n8n      ││     n8n      │
│  (UI Only)   ││  (UI Only)   ││  (UI Only)   │
└──────────────┘└──────────────┘└──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ↓
             ┌─────────────────┐
             │  Redis Queue    │
             └────────┬─────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
        ↓             ↓             ↓
┌──────────────┐┌──────────────┐┌──────────────┐
│n8n Worker 1  ││n8n Worker 2  ││n8n Worker 3  │
│ (Execution)  ││ (Execution)  ││ (Execution)  │
└──────────────┘└──────────────┘└──────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
                      ↓
             ┌─────────────────┐
             │   PostgreSQL    │
             └─────────────────┘
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Production Deployment                             │
└─────────────────────────────────────────────────────────────────────┘

Internet
    │
    ↓
┌────────────────────────────────────┐
│  Reverse Proxy (nginx/traefik)    │
│  • SSL/TLS termination             │
│  • Rate limiting                   │
│  • Load balancing                  │
│  • Static file serving             │
└────────────────────────────────────┘
    │
    ├─────────────────┬──────────────┐
    │                 │              │
    ↓                 ↓              ↓
┌─────────┐     ┌─────────┐    ┌─────────┐
│Frontend │     │ Backend │    │   n8n   │
│ (React) │     │(FastAPI)│    │         │
└─────────┘     └─────────┘    └─────────┘
                      │              │
                      └──────┬───────┘
                             │
                             ↓
                    ┌─────────────────┐
                    │   PostgreSQL    │
                    │   (Managed)     │
                    └─────────────────┘
                             │
                             ↓
                    ┌─────────────────┐
                    │  Backup Storage │
                    │  (S3/GCS)       │
                    └─────────────────┘
```

---

## Monitoring Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Monitoring Stack                                │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                         Application Layer                             │
│  ┌────────┐  ┌────────┐  ┌────────┐                                 │
│  │  n8n   │  │Backend │  │Frontend│                                  │
│  └───┬────┘  └───┬────┘  └───┬────┘                                 │
│      │           │           │                                        │
│      │ Metrics   │ Logs      │ Traces                                │
│      │           │           │                                        │
└──────┼───────────┼───────────┼────────────────────────────────────────┘
       │           │           │
       ↓           ↓           ↓
┌──────────────────────────────────────────────────────────────────────┐
│                      Collection Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ Prometheus  │  │  Loki       │  │  Jaeger     │                  │
│  │ (Metrics)   │  │  (Logs)     │  │  (Traces)   │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└──────────────────────────────────────────────────────────────────────┘
       │           │           │
       └───────────┼───────────┘
                   │
                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    Visualization Layer                                │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                        Grafana                                  │ │
│  │  • Workflow execution dashboards                               │ │
│  │  • Error rate monitoring                                       │ │
│  │  • Performance metrics                                         │ │
│  │  • Resource utilization                                        │ │
│  └────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────────────────────────────────┐
│                       Alert Layer                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │   Email     │  │   Slack     │  │ PagerDuty   │                  │
│  │   Alerts    │  │   Alerts    │  │   Alerts    │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

This architecture provides:
- **Scalability**: Queue-based execution with horizontal scaling
- **Reliability**: Health checks, retry logic, error handling
- **Security**: Multiple security layers, encryption, isolation
- **Observability**: Comprehensive logging, metrics, and tracing
- **Maintainability**: Clear component separation, documentation

All components are production-ready and designed for enterprise deployment.
