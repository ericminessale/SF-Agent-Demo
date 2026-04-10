# Architecture

## Consolidated Tools Pattern

Traditional approach: one tool per operation (28 tools for this agent). The LLM must pick
from 28 options, and selection accuracy degrades past 8 tools per step.

This agent uses **consolidated domain tools**: 9 tools, each handling multiple operations
via an `action` parameter. The LLM picks the domain (9 choices — reliable), fills in the
action enum (constrained by the parameter description), and deterministic code routes to
the correct handler.

```python
@AgentBase.tool(
    name="orders",
    description="Handle any order-related request...",
    parameters={
        "action": {
            "type": "string",
            "description": "Must be one of: list, details, update_address, cancel, confirm_cancel"
        },
        ...
    },
)
def orders(self, args, raw_data):
    action = (args.get("action") or "").lower()
    if action == "list":
        return self._list_orders(raw_data)
    elif action == "details":
        return self._get_order_details(args, raw_data)
    # ... code routes deterministically
```

Why this works:
- LLM picks from 9 tools (vs 28) — well within reliable range
- Action routing is deterministic code — PGI, not LLM judgment
- No step navigation needed — everything callable from one step
- Tool descriptions disambiguate with "NOT for X — use Y" boundaries

## PGI Enforcement (Programmatically Governed Inference)

The AI proposes, code decides. Every rule that matters is enforced in code, not prompts.

### Locked Greeting Step

```python
greeting.set_valid_steps([])  # AI cannot leave this step
greeting.set_functions(["identify_account"])  # only tool available
```

The `identify_account` tool is the only exit. It validates the account exists in
Salesforce, updates global_data, and calls `swml_change_step("route_intent")`.
The AI structurally cannot access any domain tool before identifying a customer.

### Action-Level Precondition Gating

Every consolidated tool validates state at the dispatch level before executing:

```python
def orders(self, args, raw_data):
    gd = raw_data.get("global_data", {})

    # Universal gate: all actions require identification
    if not gd.get("account_id"):
        return FunctionResult(
            "NO_ACCOUNT: Customer must be identified first. "
            "Use identify_account to look them up."
        )

    if action == "confirm_cancel":
        # Gate: requires pending preview
        if not gd.get("cancel_preview"):
            return FunctionResult(
                "NO_PREVIEW: Use orders with action='cancel' first."
            )
        return self._confirm_cancel(args, raw_data)
```

Precondition map:
- `list` actions: require `account_id`
- `details` actions: require `account_id` + identifier parameter
- `update`/`cancel` actions: require `account_id` + selected record in global_data
- `confirm_cancel`: requires pending preview in global_data
- `convert`/`update` lead: require `selected_lead_id` in global_data

### Two-Step Confirmation

Destructive operations (order cancellation) use a preview + confirm pattern:
1. `orders(action="cancel")` — shows order details, stores preview in global_data
2. `orders(action="confirm_cancel")` — checks preview exists, executes cancellation

The AI cannot skip the preview because `confirm_cancel` gates on `cancel_preview`
existing in global_data.

### Prescriptive Function Returns

Every function return tells the AI what to DO next, not just what happened:

```python
# BAD: status only
return FunctionResult("Order cancelled.")

# GOOD: prescriptive next-action
return FunctionResult(
    "CANCELLED: Order 00000125 has been cancelled and a tracking case "
    "has been created (Case #00001234). Tell the customer and ask if "
    "there's anything else you can help with."
)
```

## Tool Descriptions as LLM Instructions

Tool descriptions and parameter descriptions are the primary mechanism the LLM uses
to select which tool to call. They must:

1. Match caller language (not Salesforce terminology)
2. Draw boundaries against competing tools ("NOT for X — use Y")
3. Include the distinguishing signal for ambiguous requests

```python
name="field_service",
description=(
    "Handle work orders, technician dispatch, and asset tracking. "
    "Use when the caller needs on-site service, equipment inspection, "
    "or wants to know what products they have deployed. "
    "NOT for support tickets or complaints — use cases. "
    "NOT for purchase history — use orders."
)
```

## State Machine

```
greeting (locked)
  └── identify_account → [validates account] → swml_change_step("route_intent")

route_intent (9 domain tools)
  ├── orders(action=list/details/update_address/cancel/confirm_cancel)
  ├── cases(action=list/details/create/escalate)
  ├── leads(action=list/select/create/update/convert)
  ├── opportunities(action=list/details/update_stage/add_product)
  ├── scheduling(action=list/create_task/schedule_event/complete_task)
  ├── field_service(action=list_work_orders/create_work_order/list_assets)
  ├── search_knowledge(query)
  └── check_support_level()

wrap_up (no tools)
```

## Salesforce Integration

- **Auth**: OAuth 2.0 Client Credentials Flow via Connected App
- **Library**: simple-salesforce
- **SOQL injection prevention**: `escape_soql()` on all user input
- **Voice formatting**: dates, currency, phone numbers, order numbers, case numbers all formatted for natural TTS
- **Post-call logging**: `on_summary()` writes structured JSON to Salesforce as a Task on the Account
- **Per-call dynamic config**: Caller ID lookup pre-populates account info before the AI speaks

## Re-Anchoring Pattern

In multi-turn conversations, the LLM's attention to its tool list fades. Two mitigations:

1. Route_intent step task explicitly lists tool names:
   `"You have: orders, cases, leads, opportunities, scheduling, ..."`
2. Key function returns include: `"You still have all your tools available."`

This eliminated intermittent "I don't have access" failures in production testing.
