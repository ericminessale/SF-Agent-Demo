# SF Agent Demo

AI voice agent for comprehensive Salesforce CRM management, powered by SignalWire. One phone call handles orders, support cases, leads, opportunities, scheduling, knowledge base, field service, and entitlements — all against a live Salesforce org.

Built with the [SignalWire AI Agents SDK](https://github.com/signalwire/signalwire-python) using Programmatically Governed Inference (PGI): the AI proposes, code decides.

## What it does

9 consolidated tools handle 30+ operations across every major Salesforce domain:

| Tool | Actions | What it covers |
|------|---------|---------------|
| `identify_account` | lookup by name or phone | Caller identification with auto-detect via caller ID |
| `orders` | list, details, update_address, cancel, confirm_cancel | Order management with two-step cancellation |
| `cases` | list, details, create, escalate | Support ticket lifecycle |
| `leads` | list, select, create, update, convert | Lead management through full sales pipeline |
| `opportunities` | list, details, update_stage, add_product | Deal tracking and product attachment |
| `scheduling` | list, create_task, schedule_event, complete_task | Tasks, events, and activity management |
| `field_service` | list_work_orders, create_work_order, list_assets | On-site service and asset tracking |
| `search_knowledge` | keyword search | FAQ lookup from published Knowledge articles |
| `check_support_level` | entitlement check | Support tier and SLA verification |

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design, but the key ideas:

- **Consolidated tools** — 9 domain tools with an `action` parameter instead of 28 individual tools. The LLM picks the domain, code routes the action. This keeps tool selection reliable at scale.
- **PGI governance** — Locked greeting step (can't access domain tools without identification), action-level precondition gating in code, two-step confirmation for destructive operations, prescriptive function returns.
- **Voice-native** — Text normalization, ASR hints for Salesforce terminology, fillers on every tool, all values formatted for natural speech.
- **Post-call logging** — Structured JSON summary written back to Salesforce as a Task after every call.

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

Creates 5 accounts, 7 contacts, 10 products, 15 orders, 8 cases, 12 leads, 12 opportunities, 10 events, 5 entitlements, 5 work orders, 9 assets, and 13 Knowledge articles.

### 6. Run the agent

```bash
PYTHONUTF8=1 python agent.py
```

The agent starts on port 3000 at `/agent`. Expose with ngrok or deploy, then point a SignalWire phone number at `https://your-url/agent`.

## Demo scenarios

Try these when calling the agent:

1. **"Hi, this is Acme Corporation"** — auto-identifies the account, greets by name
2. **"Show me our recent orders"** — lists orders with voice-formatted dates and amounts
3. **"Cancel order 125"** — previews the order, asks for confirmation, creates a tracking case
4. **"Do you have docs on API rate limits?"** — searches Knowledge articles, reads the answer
5. **"Create a lead for Sarah Chen at BluePeak Software"** — creates a lead in Salesforce
6. **"What support plan are we on?"** — checks entitlements and reads back the tier
7. **"Schedule a follow-up call for tomorrow at 2 PM"** — creates an Event in Salesforce
8. **"I need a technician dispatched for a failed server"** — creates a Work Order

After hanging up, check Salesforce — there's a Task on the Account with a structured summary of the call.

## Files

| File | Purpose |
|------|---------|
| `agent.py` | The voice AI agent — 9 consolidated tools, PGI-enforced |
| `salesforce_client.py` | Salesforce REST API client (OAuth, SOQL, CRUD, voice formatting) |
| `seed_salesforce.py` | Seeds the org with demo data across all domains |
| `test_connection.py` | Verifies Salesforce API connectivity and object access |
| `SETUP_GUIDE.md` | Step-by-step Salesforce org setup (30-40 min) |
| `ARCHITECTURE.md` | Design decisions, PGI patterns, tool architecture |
