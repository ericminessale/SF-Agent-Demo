# SF Agent Demo

Multi-agent voice AI system for Salesforce CRM, powered by SignalWire. Four specialized agents handle customer service, sales, field service, and triage — each on its own route, each independently callable, all sharing caller identity seamlessly across transfers.

Built with the [SignalWire AI Agents SDK](https://github.com/signalwire/signalwire-python) using Programmatically Governed Inference (PGI): the AI proposes, code decides.

## Agents

| Agent | Route | Purpose | Tools |
|-------|-------|---------|-------|
| **Triage** | `/agent` | Identifies caller, routes to department, handles FAQ | 3 |
| **Customer Service** | `/service` | Orders, cases, support level, knowledge | 5 |
| **Sales** | `/sales` | Leads, opportunities, knowledge | 4 |
| **Field Service** | `/field-service` | Work orders, assets, scheduling, knowledge | 5 |

Each agent has 3-5 tools. Each route is directly callable — point a phone number at `/sales` for a dedicated sales line, or use `/agent` as a general number with triage routing.

**Every agent has knowledge search** — SOSL full-text search against Salesforce Knowledge articles. Callers can ask questions at any point in any department.

## What it does

**Triage** (`/agent`):
- Identify caller by name or phone
- Route to the right department seamlessly (no transfer language)
- Handle FAQ questions directly

**Customer Service** (`/service`):
- List and view order details, update shipping addresses, cancel with two-step confirmation
- Create, view, and escalate support cases
- Check support tier and entitlements

**Sales** (`/sales`):
- Create, list, select, update, and convert leads (with PGI guard against wrong company)
- List, view, update stage, and add products to opportunities

**Field Service** (`/field-service`):
- Create and list work orders for on-site service
- View deployed assets and equipment
- Schedule events, create tasks, mark tasks complete

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design. Key highlights:

- **Multi-agent on AgentServer** — 4 agents, one Python file, each at its own route
- **Seamless transfers** — custom SWML transfer tool passes identity via URL query params. Receiving agent's `dynamic_config_callback` reads params and sets global_data before the AI starts. Zero re-identification.
- **PGI governance** — locked greeting steps, action-level precondition gating, two-step cancel confirmation, prescriptive returns, PGI guard on lead company confusion
- **SOSL knowledge search** — full-text search against Salesforce Knowledge articles, with per-agent parameter descriptions guiding the LLM to pass effective queries
- **Post-call logging** — structured JSON summary written to Salesforce as a Task after every call

## Setup

### 1. Salesforce org

Follow [SETUP_GUIDE.md](SETUP_GUIDE.md) to create a free Developer Edition org, configure OAuth, enable Knowledge/Entitlements/Work Orders, and set up the Integration user.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
# Fill in: SignalWire credentials, Salesforce OAuth credentials, Google Maps API key
```

### 4. Test Salesforce connection

```bash
python test_connection.py
```

### 5. Seed demo data

```bash
python seed_salesforce.py
```

Creates accounts, contacts, products, orders, cases, leads, opportunities, events, entitlements, work orders, assets, and Knowledge articles.

### 6. Run the agents

```bash
PYTHONUTF8=1 python agent.py
```

All 4 agents start on port 3000:
- `http://localhost:3000/agent` — Triage
- `http://localhost:3000/service` — Customer Service
- `http://localhost:3000/sales` — Sales
- `http://localhost:3000/field-service` — Field Service

Expose with ngrok, then point SignalWire phone numbers at the routes.

## Demo scenarios

**General line** (call `/agent`):
1. "Hi, this is Acme Corporation" — identifies account
2. "I need to check on an order" — routes seamlessly to Customer Service
3. "Actually, I also have a question about our support plan" — handled without re-identification

**Customer Service** (call `/service` directly):
1. "Show me our recent orders" — lists with voice-formatted dates and amounts
2. "Cancel order 125" — previews, confirms, creates tracking case
3. "Do you have docs on password resets?" — searches Knowledge articles

**Sales** (call `/sales` directly):
1. "Create a lead for Sarah Chen at BluePeak Software" — creates in Salesforce
2. "Show me our open opportunities" — lists deals with stages and amounts
3. "What's the product compatibility info?" — searches Knowledge

**Field Service** (call `/field-service` directly):
1. "I need a technician dispatched for a failed server" — creates Work Order
2. "What equipment do we have deployed?" — lists assets
3. "Schedule a follow-up for next Wednesday" — creates Event

## Files

| File | Purpose |
|------|---------|
| `agent.py` | All 4 agents + shared utilities — AgentServer multi-route |
| `salesforce_client.py` | Salesforce REST API client (OAuth, SOQL, SOSL, CRUD, voice formatting) |
| `seed_salesforce.py` | Seeds the org with demo data across all domains |
| `test_connection.py` | Verifies Salesforce API connectivity and object access |
| `SETUP_GUIDE.md` | Step-by-step Salesforce org setup (45 min) |
| `ARCHITECTURE.md` | Multi-agent design, PGI patterns, transfer mechanics |
