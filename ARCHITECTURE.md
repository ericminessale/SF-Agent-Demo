# Architecture

## Multi-Agent Design

Four specialized agents on one `AgentServer`, each at its own route:

```
AgentServer (port 3000)
├── /agent          TriageAgent        — identify + route + FAQ
├── /service        CustomerServiceAgent — orders + cases + entitlements
├── /sales          SalesAgent         — leads + opportunities
└── /field-service  FieldServiceAgent  — work orders + assets + scheduling
```

Each agent has 3-5 tools. Each route is independently callable — point a phone
number directly at `/sales` for a sales-only line, or use `/agent` as a general
number with triage routing.

### Why Multi-Agent, Not One Agent

A single agent handling all domains requires 9+ tools on one step. LLM tool
selection accuracy degrades past 7-8 tools — the AI picks semantically similar
but wrong tools ~5% of the time. Multiple sessions of iteration (consolidated
tools, disambiguation descriptions, re-anchoring patterns) improved this but
never eliminated it.

Multi-agent eliminates the problem structurally: each agent has 3-5 tools, well
within the reliable range. The triage agent routes at the platform level, not
via LLM judgment.

### Agent Grouping

Agents are grouped by **caller persona**, not by Salesforce object:

| Agent | Caller | Why these tools belong together |
|-------|--------|-------------------------------|
| Customer Service | Customer calling about their account | Orders → problem → case → check support tier. One journey. |
| Sales | Sales rep managing pipeline | Find lead → qualify → convert → manage opportunity. One journey. |
| Field Service | Dispatcher or customer needing on-site work | Check assets → create work order → schedule visit. One journey. |

A caller should rarely need to hop between agents. If they do, the triage
agent handles it seamlessly.

## Seamless Transfers

### Custom Transfer Tool (Not swml_transfer Skill)

The triage agent uses a custom `route_caller` tool instead of the `swml_transfer`
skill. The skill defines static URLs at config time, but we need dynamic URLs
with identity encoded at call time.

```python
def route_caller(self, args, raw_data):
    gd = raw_data.get("global_data", {})
    url = build_transfer_url(self, route_map[dept], gd)
    # URL: /service?account_id=xxx&account_name=Acme+Corporation

    result = FunctionResult(messages[dept], post_process=True)
    # Manual SWML — no set ai_response to avoid RPC Chat "Transfer complete" text
    result.action.append({
        "SWML": {
            "version": "1.0.0",
            "sections": {"main": [{"transfer": {"dest": url}}]}
        },
        "transfer": "true"
    })
    return result
```

### Identity Passing via Query Parameters

global_data does NOT flow through SWML transfers. Identity is encoded in the
transfer URL and read by the receiving agent's `dynamic_config_callback`:

```python
# Receiving agent reads query params before AI starts
def shared_per_call_config(query_params, body_params, headers, agent):
    account_id = query_params.get("account_id", "")
    if account_id:
        # Transfer — identity already known, skip greeting
        agent.set_global_data({"account_id": account_id, "identified": True, ...})
        agent.prompt_add_section("Caller Info",
            body=f"The caller is {account_name}. Say their name and ask how to help."
        )
    else:
        # Direct call — try auto-detect from phone, fall back to greeting
```

### Three Identification States

| State | Source | Greeting Behavior |
|-------|--------|------------------|
| Transfer (identified=True) | Query params from triage | Skip greeting, say name, ask how to help |
| Auto-detected (auto_detected_name set) | Phone number match | Greet warmly, confirm: "Is this Acme Corporation?" |
| Unknown | Direct call, no phone match | Greet warmly, ask for name or phone |

### Zero Transfer Language

The triage agent never says "transferring," "connecting," or names departments.
The `route_caller` tool's description and FunctionResult avoid all transfer
language. From the caller's perspective, it's one continuous conversation.

Department names were removed from all tool descriptions and returns. The AI
routes using internal department codes, not spoken names.

## PGI Enforcement

### Locked Greeting Steps

```python
greeting.set_valid_steps([])  # AI cannot leave
greeting.set_functions(["identify_account"])  # only tool
# identify_account success → swml_change_step("route_intent")
```

### Action-Level Precondition Gating

Each consolidated tool validates state before dispatching:
- All actions require `account_id` (identification must succeed first)
- `cancel` requires order selection
- `confirm_cancel` requires pending preview
- `update`/`convert` lead requires `selected_lead_id`
- `update_stage`/`add_product` opportunity requires `selected_opp_id`

### PGI Guard: Lead Company Confusion

Both prompt-level AND code-level enforcement:
- Prompt: "If caller asks to create a lead at their own company, remind them leads are for NEW prospects"
- Code: Tool validates `company != global_data.account_name`, returns `WRONG_COMPANY` error

### Two-Step Cancel Confirmation

```
orders(action="cancel") → preview, store in global_data
orders(action="confirm_cancel") → gate on pending preview, execute
```

### Prescriptive Function Returns

Every return tells the AI what to DO next:
```python
return FunctionResult(
    f"CANCELLED: Order {number} cancelled. Case #{case} created for tracking. "
    "Tell the caller and ask if there's anything else."
)
```

## Knowledge Search (SOSL)

Each agent has a `search_knowledge` tool that uses Salesforce SOSL (full-text
search) instead of SOQL LIKE (substring match):

```python
results = sf.search(
    f"FIND {{{safe_query}}} IN ALL FIELDS "
    "RETURNING Knowledge__kav(Id, Title, Summary "
    "WHERE PublishStatus = 'Online') LIMIT 3"
)
```

The parameter description guides the LLM to pass effective queries:
```
"One or two specific keywords from the caller's question. Pass the most
distinctive noun or phrase. Examples: 'password', 'billing', 'API rate limits'"
```

## Post-Call Logging

`on_summary()` writes a structured JSON Task to Salesforce:
- Subject: "Call Summary — {account_name} ({agent_type})"
- Description: JSON with actions taken, resolution, follow-up needed
- Priority: Normal (not sentiment-driven — LLM sentiment is unverified)
- Linked to Account via WhatId
