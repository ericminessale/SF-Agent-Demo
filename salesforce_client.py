"""
Salesforce client module for the Salesforce Super-Agent.
Handles OAuth authentication and all CRUD operations against the Salesforce REST API.
Covers: Accounts, Contacts, Orders, Cases, Leads, Opportunities, Tasks, Events, Campaigns, Knowledge.
"""

import os
import re
import logging
import requests
from datetime import datetime, timedelta

log = logging.getLogger("salesforce-client")
from simple_salesforce import Salesforce
from simple_salesforce.exceptions import (
    SalesforceResourceNotFound, SalesforceGeneralError, SalesforceMalformedRequest
)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def get_salesforce_client() -> Salesforce:
    """Authenticate via Client Credentials Flow and return a Salesforce client."""
    client_id = os.getenv("SALESFORCE_CLIENT_ID")
    client_secret = os.getenv("SALESFORCE_CLIENT_SECRET")
    instance_url = os.getenv("SALESFORCE_INSTANCE_URL")

    if not all([client_id, client_secret, instance_url]):
        raise ValueError(
            "Missing SALESFORCE_CLIENT_ID, SALESFORCE_CLIENT_SECRET, or SALESFORCE_INSTANCE_URL in .env"
        )

    resp = requests.post(f"{instance_url}/services/oauth2/token", data={
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    })

    if resp.status_code != 200:
        raise Exception(f"OAuth failed ({resp.status_code}): {resp.text}")

    token_data = resp.json()
    canonical_url = token_data.get("instance_url", instance_url)
    return Salesforce(instance_url=canonical_url, session_id=token_data["access_token"])


# ---------------------------------------------------------------------------
# SOQL helpers
# ---------------------------------------------------------------------------

def escape_soql(value: str) -> str:
    """Escape user input for safe SOQL interpolation."""
    if not value:
        return ""
    return value.replace("\\", "\\\\").replace("'", "\\'")


def normalize_phone(phone: str) -> str:
    """Strip a phone string to 10 US digits."""
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("1") and len(digits) == 11:
        digits = digits[1:]
    return digits


# ---------------------------------------------------------------------------
# Voice formatting helpers
# ---------------------------------------------------------------------------

def format_phone_for_voice(phone: str) -> str:
    """Format phone for voice: '5551001000' -> '555, 100, 1000'."""
    d = normalize_phone(phone)
    if len(d) == 10:
        return f"{d[:3]}, {d[3:6]}, {d[6:]}"
    return phone


def format_currency_for_voice(amount) -> str:
    """Format currency so text normalization speaks it naturally."""
    if amount is None:
        return "unknown amount"
    try:
        val = float(amount)
        if val == int(val):
            return f"${int(val):,}"
        return f"${val:,.2f}"
    except (ValueError, TypeError):
        return str(amount)


def format_date_for_voice(date_str: str) -> str:
    """Convert '2026-04-08' -> 'April 8, 2026'."""
    if not date_str:
        return "no date set"
    try:
        dt = datetime.strptime(date_str[:10], "%Y-%m-%d")
        return dt.strftime("%B %-d, %Y") if os.name != "nt" else dt.strftime("%B %#d, %Y")
    except (ValueError, TypeError):
        return date_str


def format_datetime_for_voice(dt_str: str) -> str:
    """Convert ISO datetime -> 'April 8, 2026 at 2:00 PM'."""
    if not dt_str:
        return "no date set"
    try:
        # Salesforce returns '2026-04-08T14:00:00.000+0000'
        clean = dt_str.replace("+0000", "+00:00").replace(".000+", "+")
        dt = datetime.fromisoformat(clean.replace("Z", "+00:00"))
        date_part = dt.strftime("%B %#d, %Y") if os.name == "nt" else dt.strftime("%B %-d, %Y")
        time_part = dt.strftime("%#I:%M %p") if os.name == "nt" else dt.strftime("%-I:%M %p")
        return f"{date_part} at {time_part}"
    except (ValueError, TypeError):
        return dt_str


def format_order_number(order_num: str) -> str:
    """Format order number for voice: '00000123' -> '123'."""
    if not order_num:
        return "unknown"
    return str(int(re.sub(r"\D", "", order_num))) if re.sub(r"\D", "", order_num) else order_num


def format_case_number(case_num: str) -> str:
    """Format case number for voice: '00001234' -> '1234'."""
    if not case_num:
        return "unknown"
    return str(int(re.sub(r"\D", "", case_num))) if re.sub(r"\D", "", case_num) else case_num


def format_address(addr: dict) -> str:
    """Format Salesforce compound address for voice."""
    if not addr:
        return "no address on file"
    parts = []
    if addr.get("street"):
        parts.append(addr["street"])
    if addr.get("city"):
        parts.append(addr["city"])
    if addr.get("stateCode") or addr.get("state"):
        parts.append(addr.get("stateCode") or addr.get("state"))
    if addr.get("postalCode"):
        parts.append(addr["postalCode"])
    return ", ".join(parts) if parts else "no address on file"


# ---------------------------------------------------------------------------
# US States for address normalization
# ---------------------------------------------------------------------------

US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}


# ---------------------------------------------------------------------------
# Account / Contact queries
# ---------------------------------------------------------------------------

def lookup_account_by_phone(sf: Salesforce, phone: str) -> dict | None:
    digits = normalize_phone(phone)
    if not digits:
        return None
    safe = escape_soql(digits)
    result = sf.query(
        f"SELECT Id, Name, Phone, Industry, BillingAddress, AccountNumber "
        f"FROM Account WHERE Phone = '{safe}' LIMIT 1"
    )
    return result["records"][0] if result["records"] else None


def lookup_account_by_name(sf: Salesforce, name: str) -> list:
    """Return up to 5 matching accounts (partial match)."""
    safe = escape_soql(name)
    result = sf.query(
        f"SELECT Id, Name, Phone, Industry, BillingAddress "
        f"FROM Account WHERE Name LIKE '%{safe}%' LIMIT 5"
    )
    return result["records"]


def get_contacts_for_account(sf: Salesforce, account_id: str) -> list:
    safe = escape_soql(account_id)
    result = sf.query(
        f"SELECT Id, FirstName, LastName, Email, Phone, Title "
        f"FROM Contact WHERE AccountId = '{safe}'"
    )
    return result["records"]


def lookup_contact_by_name(sf: Salesforce, name: str, account_id: str = None) -> list:
    safe_name = escape_soql(name)
    where = f"Name LIKE '%{safe_name}%'"
    if account_id:
        safe_acct = escape_soql(account_id)
        where += f" AND AccountId = '{safe_acct}'"
    result = sf.query(
        f"SELECT Id, FirstName, LastName, Email, Phone, Title, Account.Name "
        f"FROM Contact WHERE {where} LIMIT 5"
    )
    return result["records"]


# ---------------------------------------------------------------------------
# Order queries
# ---------------------------------------------------------------------------

def get_orders_for_account(sf: Salesforce, account_id: str) -> list:
    safe = escape_soql(account_id)
    result = sf.query(
        f"SELECT Id, OrderNumber, Status, TotalAmount, EffectiveDate, "
        f"ShippingAddress, Description "
        f"FROM Order WHERE AccountId = '{safe}' "
        f"ORDER BY EffectiveDate DESC LIMIT 10"
    )
    return result["records"]


def get_order_by_number(sf: Salesforce, order_number: str) -> dict | None:
    safe = escape_soql(order_number)
    result = sf.query(
        f"SELECT Id, OrderNumber, Status, TotalAmount, EffectiveDate, "
        f"ShippingAddress, Description, Account.Name, Account.Id "
        f"FROM Order WHERE OrderNumber = '{safe}' LIMIT 1"
    )
    return result["records"][0] if result["records"] else None


def get_order_items(sf: Salesforce, order_id: str) -> list:
    safe = escape_soql(order_id)
    result = sf.query(
        f"SELECT Id, OrderItemNumber, Quantity, UnitPrice, TotalPrice, "
        f"Product2.Name, Product2.ProductCode "
        f"FROM OrderItem WHERE OrderId = '{safe}'"
    )
    return result["records"]


def update_order_shipping(sf: Salesforce, order_id: str, street: str,
                          city: str, state: str, postal_code: str) -> bool:
    state_full = US_STATES.get(state.upper(), state) if len(state) <= 2 else state
    try:
        sf.Order.update(order_id, {
            "ShippingStreet": street,
            "ShippingCity": city,
            "ShippingState": state_full,
            "ShippingPostalCode": postal_code,
            "ShippingCountry": "United States",
        })
        return True
    except Exception:
        return False


def cancel_order(sf: Salesforce, order_id: str) -> dict:
    """Cancel a draft order. Returns {'success': bool, 'message': str, 'case_id': str|None}."""
    try:
        order = sf.Order.get(order_id)
    except SalesforceResourceNotFound:
        return {"success": False, "message": "Order not found", "case_id": None}

    status = order.get("Status", "")
    if status != "Draft":
        return {
            "success": False,
            "message": f"Only draft orders can be cancelled. This order is {status}.",
            "case_id": None,
        }

    account_id = order.get("AccountId")
    order_number = order.get("OrderNumber", "unknown")

    # Delete order items first (required before deleting order)
    items = sf.query(f"SELECT Id FROM OrderItem WHERE OrderId = '{escape_soql(order_id)}'")
    for item in items["records"]:
        sf.OrderItem.delete(item["Id"])
    sf.Order.delete(order_id)

    # Create tracking case
    case_id = None
    if account_id:
        try:
            case_result = sf.Case.create({
                "AccountId": account_id,
                "Subject": f"Order {order_number} cancelled by customer",
                "Description": f"Customer requested cancellation of draft order {order_number} via phone.",
                "Status": "New",
                "Priority": "Low",
                "Origin": "Phone",
            })
            case_id = case_result["id"]
        except Exception:
            pass

    return {"success": True, "message": f"Order {order_number} has been cancelled.", "case_id": case_id}


# ---------------------------------------------------------------------------
# Case queries
# ---------------------------------------------------------------------------

def get_cases_for_account(sf: Salesforce, account_id: str) -> list:
    safe = escape_soql(account_id)
    result = sf.query(
        f"SELECT Id, CaseNumber, Subject, Status, Priority, Description, CreatedDate "
        f"FROM Case WHERE AccountId = '{safe}' AND IsClosed = false "
        f"ORDER BY CreatedDate DESC LIMIT 10"
    )
    return result["records"]


def get_case_by_number(sf: Salesforce, case_number: str) -> dict | None:
    safe = escape_soql(case_number)
    result = sf.query(
        f"SELECT Id, CaseNumber, Subject, Status, Priority, Description, "
        f"CreatedDate, Account.Name, Account.Id "
        f"FROM Case WHERE CaseNumber = '{safe}' LIMIT 1"
    )
    return result["records"][0] if result["records"] else None


def create_case(sf: Salesforce, account_id: str, subject: str,
                description: str, priority: str = "Medium") -> dict:
    """Create a support case. Returns {'id': str, 'case_number': str}."""
    valid_priorities = ["Low", "Medium", "High", "Critical"]
    if priority not in valid_priorities:
        priority = "Medium"
    result = sf.Case.create({
        "AccountId": account_id,
        "Subject": subject,
        "Description": description,
        "Status": "New",
        "Priority": priority,
        "Origin": "Phone",
    })
    case_detail = sf.query(f"SELECT CaseNumber FROM Case WHERE Id = '{result['id']}' LIMIT 1")
    case_number = case_detail["records"][0]["CaseNumber"] if case_detail["records"] else "unknown"
    return {"id": result["id"], "case_number": case_number}


def escalate_case(sf: Salesforce, case_id: str) -> bool:
    try:
        sf.Case.update(case_id, {"Priority": "High"})
        return True
    except Exception:
        return False


def add_case_comment(sf: Salesforce, case_id: str, comment: str) -> bool:
    try:
        sf.CaseComment.create({
            "ParentId": case_id,
            "CommentBody": comment,
            "IsPublished": False,
        })
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Lead queries
# ---------------------------------------------------------------------------

def create_lead(sf: Salesforce, first_name: str, last_name: str, company: str,
                phone: str = None, email: str = None, description: str = None) -> dict:
    """Create a new lead. Handles Salesforce duplicate detection. Returns {'id': str, 'duplicate': bool}."""
    data = {
        "FirstName": first_name,
        "LastName": last_name,
        "Company": company,
        "Status": "Open - Not Contacted",
        "LeadSource": "Phone Inquiry",
    }
    if phone:
        data["Phone"] = normalize_phone(phone)
    if email:
        data["Email"] = email
    if description:
        data["Description"] = description
    try:
        result = sf.Lead.create(data)
        return {"id": result["id"], "duplicate": False}
    except (SalesforceGeneralError, SalesforceMalformedRequest) as e:
        # Handle Salesforce duplicate detection rules (returns HTTP 400)
        if "DUPLICATES_DETECTED" in str(e) or "duplicateResult" in str(e):
            result = sf.Lead.create(data, headers={"Sforce-Duplicate-Rule-Header": "allowSave=true"})
            return {"id": result["id"], "duplicate": True}
        raise


def list_leads(sf: Salesforce, status: str = None, limit: int = 15) -> list:
    where = ""
    if status:
        safe = escape_soql(status)
        where = f"WHERE Status = '{safe}' "
    result = sf.query(
        f"SELECT Id, FirstName, LastName, Company, Status, Phone, Email, "
        f"LeadSource, CreatedDate "
        f"FROM Lead {where}"
        f"ORDER BY CreatedDate DESC LIMIT {limit}"
    )
    return result["records"]


def search_lead_by_name(sf: Salesforce, name: str) -> list:
    """Search leads by name (partial match). Returns up to 5."""
    safe = escape_soql(name)
    result = sf.query(
        f"SELECT Id, FirstName, LastName, Company, Status, Phone, Email "
        f"FROM Lead WHERE Name LIKE '%{safe}%' "
        f"ORDER BY CreatedDate DESC LIMIT 5"
    )
    return result["records"]


def get_lead(sf: Salesforce, lead_id: str) -> dict | None:
    try:
        return sf.Lead.get(lead_id)
    except SalesforceResourceNotFound:
        return None


def update_lead_status(sf: Salesforce, lead_id: str, status: str) -> bool:
    valid = ["Open - Not Contacted", "Working - Contacted", "Closed - Converted",
             "Closed - Not Converted"]
    if status not in valid:
        return False
    try:
        sf.Lead.update(lead_id, {"Status": status})
        return True
    except Exception:
        return False



# ---------------------------------------------------------------------------
# Opportunity queries
# ---------------------------------------------------------------------------

def list_opportunities(sf: Salesforce, account_id: str) -> list:
    safe = escape_soql(account_id)
    result = sf.query(
        f"SELECT Id, Name, StageName, Amount, CloseDate, Probability, "
        f"Description "
        f"FROM Opportunity WHERE AccountId = '{safe}' "
        f"ORDER BY CloseDate DESC LIMIT 10"
    )
    return result["records"]


def search_opportunity_by_name(sf: Salesforce, name: str, account_id: str = None) -> dict | None:
    """Search for a single opportunity by partial name match. Returns first match or None."""
    safe_name = escape_soql(name)
    where = f"Name LIKE '%{safe_name}%'"
    if account_id:
        where += f" AND AccountId = '{escape_soql(account_id)}'"
    result = sf.query(
        f"SELECT Id, Name, StageName, Amount, CloseDate, Probability, Description "
        f"FROM Opportunity WHERE {where} LIMIT 1"
    )
    return result["records"][0] if result["records"] else None


def get_opportunity(sf: Salesforce, opp_id: str) -> dict | None:
    try:
        return sf.Opportunity.get(opp_id)
    except SalesforceResourceNotFound:
        return None


def get_opportunity_line_items(sf: Salesforce, opp_id: str) -> list:
    safe = escape_soql(opp_id)
    result = sf.query(
        f"SELECT Id, Name, Quantity, UnitPrice, TotalPrice, "
        f"Product2.Name, Product2.ProductCode "
        f"FROM OpportunityLineItem WHERE OpportunityId = '{safe}'"
    )
    return result["records"]


VALID_STAGES = [
    "Prospecting", "Qualification", "Needs Analysis", "Value Proposition",
    "Id. Decision Makers", "Perception Analysis", "Proposal/Price Quote",
    "Negotiation/Review", "Closed Won", "Closed Lost",
]


def update_opportunity_stage(sf: Salesforce, opp_id: str, stage: str) -> bool:
    if stage not in VALID_STAGES:
        return False
    try:
        sf.Opportunity.update(opp_id, {"StageName": stage})
        return True
    except Exception:
        return False


def add_opportunity_product(sf: Salesforce, opp_id: str, product_name: str,
                            quantity: int = 1) -> dict:
    """Add a product to an opportunity by product name.
    Returns {'success': bool, 'message': str}.
    """
    safe_name = escape_soql(product_name)
    products = sf.query(
        f"SELECT Id, Name FROM Product2 WHERE Name LIKE '%{safe_name}%' AND IsActive = true LIMIT 1"
    )
    # Retry with colon variant for voice input: "SLA Platinum" -> "SLA: Platinum"
    if not products["records"] and " " in product_name:
        colon_name = escape_soql(product_name.replace(" ", ": ", 1))
        products = sf.query(
            f"SELECT Id, Name FROM Product2 WHERE Name LIKE '%{colon_name}%' AND IsActive = true LIMIT 1"
        )
    if not products["records"]:
        return {"success": False, "message": f"Product '{product_name}' not found in catalog."}

    product_id = products["records"][0]["Id"]
    product_name_found = products["records"][0]["Name"]

    # Find pricebook entry
    pb = sf.query("SELECT Id FROM Pricebook2 WHERE IsStandard = true LIMIT 1")
    if not pb["records"]:
        return {"success": False, "message": "No standard pricebook found."}
    pb_id = pb["records"][0]["Id"]

    pbe = sf.query(
        f"SELECT Id, UnitPrice FROM PricebookEntry "
        f"WHERE Product2Id = '{escape_soql(product_id)}' "
        f"AND Pricebook2Id = '{escape_soql(pb_id)}' AND IsActive = true LIMIT 1"
    )
    if not pbe["records"]:
        return {"success": False, "message": f"No price found for {product_name_found}."}

    pbe_id = pbe["records"][0]["Id"]
    unit_price = pbe["records"][0]["UnitPrice"]

    # Ensure opportunity has the standard pricebook
    try:
        sf.Opportunity.update(opp_id, {"Pricebook2Id": pb_id})
    except Exception:
        pass  # May already be set

    try:
        sf.OpportunityLineItem.create({
            "OpportunityId": opp_id,
            "PricebookEntryId": pbe_id,
            "Quantity": quantity,
            "UnitPrice": unit_price,
        })
        return {
            "success": True,
            "message": f"Added {quantity}x {product_name_found} at {format_currency_for_voice(unit_price)} each.",
        }
    except Exception as e:
        log.error(f"add_opportunity_product error: {e}")
        return {"success": False, "message": "Could not add the product due to a system error. Please try again."}


# ---------------------------------------------------------------------------
# Task / Event queries
# ---------------------------------------------------------------------------

def create_task_record(sf: Salesforce, what_id: str, subject: str,
                       description: str = None, due_date: str = None,
                       priority: str = "Normal", who_id: str = None) -> dict:
    """Create a task. Returns {'id': str}."""
    data = {
        "WhatId": what_id,
        "Subject": subject,
        "Status": "Not Started",
        "Priority": priority,
    }
    if description:
        data["Description"] = description
    if due_date:
        data["ActivityDate"] = due_date
    if who_id:
        data["WhoId"] = who_id
    result = sf.Task.create(data)
    return {"id": result["id"]}


def create_event_record(sf: Salesforce, what_id: str, subject: str,
                        start_datetime: str, duration_minutes: int = 60,
                        description: str = None, who_id: str = None) -> dict:
    """Create a calendar event. start_datetime in ISO format. Returns {'id': str}."""
    try:
        start = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        start = datetime.now() + timedelta(days=1)
        start = start.replace(hour=10, minute=0, second=0, microsecond=0)

    end = start + timedelta(minutes=duration_minutes)

    data = {
        "WhatId": what_id,
        "Subject": subject,
        "StartDateTime": start.isoformat(),
        "EndDateTime": end.isoformat(),
        "DurationInMinutes": duration_minutes,
    }
    if description:
        data["Description"] = description
    if who_id:
        data["WhoId"] = who_id
    result = sf.Event.create(data)
    return {"id": result["id"]}


def list_tasks_for_account(sf: Salesforce, account_id: str, include_closed: bool = False) -> list:
    safe = escape_soql(account_id)
    closed_filter = "" if include_closed else "AND IsClosed = false "
    result = sf.query(
        f"SELECT Id, Subject, Status, Priority, ActivityDate, Description "
        f"FROM Task WHERE WhatId = '{safe}' {closed_filter}"
        f"ORDER BY ActivityDate ASC NULLS LAST LIMIT 15"
    )
    return result["records"]


def list_events_for_account(sf: Salesforce, account_id: str) -> list:
    safe = escape_soql(account_id)
    result = sf.query(
        f"SELECT Id, Subject, StartDateTime, EndDateTime, Location, Description "
        f"FROM Event WHERE WhatId = '{safe}' AND StartDateTime >= TODAY "
        f"ORDER BY StartDateTime ASC LIMIT 10"
    )
    return result["records"]


def complete_task(sf: Salesforce, task_id: str) -> bool:
    try:
        sf.Task.update(task_id, {"Status": "Completed"})
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Campaign queries
# ---------------------------------------------------------------------------

def list_campaigns(sf: Salesforce) -> list:
    result = sf.query(
        "SELECT Id, Name, Status, Type, StartDate, EndDate, NumberOfContacts, NumberOfLeads "
        "FROM Campaign WHERE IsActive = true ORDER BY StartDate DESC LIMIT 10"
    )
    return result["records"]


def add_campaign_member(sf: Salesforce, campaign_id: str,
                        contact_id: str = None, lead_id: str = None) -> dict:
    """Add a contact or lead to a campaign. Returns {'success': bool, 'message': str}."""
    if not contact_id and not lead_id:
        return {"success": False, "message": "Must provide either a contact or lead ID."}
    data = {"CampaignId": campaign_id, "Status": "Sent"}
    if contact_id:
        data["ContactId"] = contact_id
    elif lead_id:
        data["LeadId"] = lead_id
    try:
        sf.CampaignMember.create(data)
        return {"success": True, "message": "Successfully added to campaign."}
    except SalesforceGeneralError as e:
        if "DUPLICATE" in str(e):
            return {"success": False, "message": "This person is already a member of that campaign."}
        return {"success": False, "message": f"Failed to add to campaign: {e}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to add to campaign: {e}"}


# ---------------------------------------------------------------------------
# Knowledge (graceful degradation if not enabled)
# ---------------------------------------------------------------------------

def search_knowledge(sf: Salesforce, query: str) -> list:
    """Search knowledge articles using SOSL full-text search.
    SOSL handles word order, partial matches, and relevance ranking.
    Returns empty list if Knowledge is not enabled."""
    safe_query = escape_soql(query)
    try:
        sosl = (
            f"FIND {{{safe_query}}} IN ALL FIELDS "
            f"RETURNING Knowledge__kav(Id, Title, Summary, UrlName, ArticleNumber, PublishStatus "
            f"WHERE PublishStatus = 'Online' AND Language = 'en_US' LIMIT 5)"
        )
        result = sf.search(sosl)
        if result and result.get("searchRecords"):
            return result["searchRecords"]
    except Exception:
        pass
    return []


def get_knowledge_article(sf: Salesforce, article_id: str) -> dict | None:
    """Get a single Knowledge article by Id."""
    try:
        return sf.Knowledge__kav.get(article_id)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Entitlements
# ---------------------------------------------------------------------------

def get_entitlements_for_account(sf: Salesforce, account_id: str) -> list:
    """Get active entitlements for an account. Returns empty list if Entitlements not enabled."""
    safe = escape_soql(account_id)
    try:
        result = sf.query(
            f"SELECT Id, Name, Status, Type, StartDate, EndDate "
            f"FROM Entitlement "
            f"WHERE AccountId = '{safe}' AND Status = 'Active' "
            f"ORDER BY EndDate DESC LIMIT 5"
        )
        return result["records"]
    except Exception:
        return []


def format_entitlement_for_voice(ent: dict) -> str:
    """Format an entitlement record for voice readback."""
    name = ent.get("Name", "Unknown")
    ent_type = ent.get("Type") or "Standard"
    end = format_date_for_voice(ent.get("EndDate", ""))
    return f"{name} ({ent_type} support, active through {end})"


# ---------------------------------------------------------------------------
# Work Orders
# ---------------------------------------------------------------------------

def list_work_orders(sf: Salesforce, account_id: str) -> list:
    """List work orders for an account. Returns empty list if WorkOrder not enabled."""
    safe = escape_soql(account_id)
    try:
        result = sf.query(
            f"SELECT Id, WorkOrderNumber, Status, Subject, Description, StartDate, EndDate "
            f"FROM WorkOrder WHERE AccountId = '{safe}' "
            f"ORDER BY CreatedDate DESC LIMIT 10"
        )
        return result["records"]
    except Exception:
        return []


def create_work_order(sf: Salesforce, account_id: str, subject: str,
                      description: str = None, priority: str = "Medium") -> dict:
    """Create a work order. Returns {'id': str, 'number': str}."""
    data = {
        "AccountId": account_id,
        "Subject": subject,
        "Status": "New",
        "Priority": priority,
    }
    if description:
        data["Description"] = description
    try:
        result = sf.WorkOrder.create(data)
        wo_id = result["id"]
        detail = sf.query(f"SELECT WorkOrderNumber FROM WorkOrder WHERE Id = '{wo_id}' LIMIT 1")
        number = detail["records"][0]["WorkOrderNumber"] if detail["records"] else "unknown"
        return {"id": wo_id, "number": number}
    except Exception as e:
        log.error(f"create_work_order error: {e}")
        return {"id": None, "number": None, "error": "Could not create work order due to a system error."}


# ---------------------------------------------------------------------------
# Assets
# ---------------------------------------------------------------------------

def list_assets(sf: Salesforce, account_id: str) -> list:
    """List assets owned by an account."""
    safe = escape_soql(account_id)
    try:
        result = sf.query(
            f"SELECT Id, Name, Status, SerialNumber, Product2.Name, Quantity, "
            f"PurchaseDate, InstallDate, Description "
            f"FROM Asset WHERE AccountId = '{safe}' "
            f"ORDER BY PurchaseDate DESC NULLS LAST LIMIT 10"
        )
        return result["records"]
    except Exception:
        return []


def create_asset(sf: Salesforce, account_id: str, name: str,
                 product_id: str = None, serial_number: str = None,
                 quantity: float = 1, status: str = "Installed") -> dict:
    """Create an asset record. Returns {'id': str}."""
    data = {
        "AccountId": account_id,
        "Name": name,
        "Status": status,
        "Quantity": quantity,
    }
    if product_id:
        data["Product2Id"] = product_id
    if serial_number:
        data["SerialNumber"] = serial_number
    result = sf.Asset.create(data)
    return {"id": result["id"]}
