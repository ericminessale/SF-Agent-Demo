"""
Seed the Salesforce Developer Edition org with comprehensive demo data
for the Salesforce Super-Agent.

Creates: Accounts, Contacts, Products, PricebookEntries, Orders, OrderItems,
         Cases, Leads, Opportunities, OpportunityLineItems, Tasks, Events, Campaigns.

Usage:
    cd agents/salesforce-agent
    python seed_salesforce.py

If any API calls fail with INSUFFICIENT_ACCESS, the user must update the
Permission Set in Salesforce Setup to grant the Integration user access.
"""

import os
import sys
import random
from pathlib import Path
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from salesforce_client import get_salesforce_client, escape_soql


def seed_accounts(sf, pricebook_id):
    """Create or find demo accounts. Returns list of (account_id, account_data) tuples."""
    print("\n--- Accounts ---")
    accounts_data = [
        {"Name": "Acme Corporation", "Phone": "5551001000", "Industry": "Technology",
         "BillingStreet": "100 Innovation Dr", "BillingCity": "San Francisco",
         "BillingStateCode": "CA", "BillingPostalCode": "94105", "BillingCountryCode": "US"},
        {"Name": "Globex Industries", "Phone": "5551002000", "Industry": "Manufacturing",
         "BillingStreet": "250 Industrial Blvd", "BillingCity": "Austin",
         "BillingStateCode": "TX", "BillingPostalCode": "73301", "BillingCountryCode": "US"},
        {"Name": "Initech Solutions", "Phone": "5551003000", "Industry": "Consulting",
         "BillingStreet": "500 Business Park Way", "BillingCity": "Chicago",
         "BillingStateCode": "IL", "BillingPostalCode": "60601", "BillingCountryCode": "US"},
        {"Name": "Wayne Enterprises", "Phone": "5551004000", "Industry": "Finance",
         "BillingStreet": "1 Gotham Plaza", "BillingCity": "New York",
         "BillingStateCode": "NY", "BillingPostalCode": "10001", "BillingCountryCode": "US"},
        {"Name": "Stark Solutions", "Phone": "5551005000", "Industry": "Technology",
         "BillingStreet": "200 Malibu Point", "BillingCity": "Malibu",
         "BillingStateCode": "CA", "BillingPostalCode": "90265", "BillingCountryCode": "US"},
    ]

    results = []
    for acct in accounts_data:
        existing = sf.query(f"SELECT Id FROM Account WHERE Name = '{escape_soql(acct['Name'])}' LIMIT 1")
        if existing["records"]:
            aid = existing["records"][0]["Id"]
            print(f"  [exists] {acct['Name']}")
        else:
            r = sf.Account.create(acct)
            aid = r["id"]
            print(f"  [created] {acct['Name']}")
        results.append((aid, acct))
    return results


def seed_contacts(sf, accounts):
    """Create contacts. Returns list of (contact_id, account_idx) tuples."""
    print("\n--- Contacts ---")
    contacts_data = [
        {"FirstName": "John", "LastName": "Smith", "Email": "john.smith@acme.com",
         "Phone": "5551001001", "Title": "VP of Engineering", "AccountIdx": 0},
        {"FirstName": "Sarah", "LastName": "Johnson", "Email": "sarah.j@globex.com",
         "Phone": "5551002001", "Title": "Operations Director", "AccountIdx": 1},
        {"FirstName": "Mike", "LastName": "Williams", "Email": "mike.w@initech.com",
         "Phone": "5551003001", "Title": "CTO", "AccountIdx": 2},
        {"FirstName": "Diana", "LastName": "Prince", "Email": "diana.p@wayne.com",
         "Phone": "5551004001", "Title": "CFO", "AccountIdx": 3},
        {"FirstName": "Tony", "LastName": "Parker", "Email": "tony.p@stark.com",
         "Phone": "5551005001", "Title": "CEO", "AccountIdx": 4},
        {"FirstName": "Jane", "LastName": "Doe", "Email": "jane.doe@acme.com",
         "Phone": "5551001002", "Title": "Project Manager", "AccountIdx": 0},
        {"FirstName": "Bob", "LastName": "Martinez", "Email": "bob.m@globex.com",
         "Phone": "5551002002", "Title": "Sales Manager", "AccountIdx": 1},
    ]

    results = []
    for c in contacts_data:
        acct_idx = c.pop("AccountIdx")
        c["AccountId"] = accounts[acct_idx][0]
        existing = sf.query(f"SELECT Id FROM Contact WHERE Email = '{escape_soql(c['Email'])}' LIMIT 1")
        if existing["records"]:
            cid = existing["records"][0]["Id"]
            print(f"  [exists] {c['FirstName']} {c['LastName']}")
        else:
            r = sf.Contact.create(c)
            cid = r["id"]
            print(f"  [created] {c['FirstName']} {c['LastName']}")
        results.append((cid, acct_idx))
    return results


def seed_products(sf, pricebook_id):
    """Create products and pricebook entries. Returns list of (product_id, price) tuples."""
    print("\n--- Products ---")
    products_data = [
        {"Name": "Enterprise Server License", "ProductCode": "ENT-SRV-001",
         "Description": "Annual enterprise server license", "IsActive": True, "Price": 4999.00},
        {"Name": "Cloud Storage - 1TB", "ProductCode": "CLD-STR-001",
         "Description": "1TB cloud storage annual plan", "IsActive": True, "Price": 1200.00},
        {"Name": "API Gateway Pro", "ProductCode": "API-GW-001",
         "Description": "API gateway with 10M requests/month", "IsActive": True, "Price": 2499.00},
        {"Name": "Security Suite Premium", "ProductCode": "SEC-STE-001",
         "Description": "Advanced security and compliance suite", "IsActive": True, "Price": 3499.00},
        {"Name": "Analytics Dashboard", "ProductCode": "ANL-DSH-001",
         "Description": "Real-time analytics and reporting", "IsActive": True, "Price": 899.00},
        {"Name": "Support Plan - Gold", "ProductCode": "SUP-GLD-001",
         "Description": "24/7 support with 1-hour SLA", "IsActive": True, "Price": 1999.00},
        {"Name": "DevOps Toolkit", "ProductCode": "DEV-TK-001",
         "Description": "CI/CD pipeline and monitoring", "IsActive": True, "Price": 1599.00},
        {"Name": "Data Migration Service", "ProductCode": "DAT-MIG-001",
         "Description": "One-time data migration package", "IsActive": True, "Price": 7500.00},
        {"Name": "Training Package - 10 seats", "ProductCode": "TRN-PKG-001",
         "Description": "10-seat training and certification", "IsActive": True, "Price": 2999.00},
        {"Name": "Custom Integration Setup", "ProductCode": "CUS-INT-001",
         "Description": "Custom API integration development", "IsActive": True, "Price": 12000.00},
    ]

    results = []
    for prod in products_data:
        price = prod.pop("Price")
        existing = sf.query(f"SELECT Id FROM Product2 WHERE ProductCode = '{prod['ProductCode']}' LIMIT 1")
        if existing["records"]:
            pid = existing["records"][0]["Id"]
            print(f"  [exists] {prod['Name']}")
        else:
            r = sf.Product2.create(prod)
            pid = r["id"]
            print(f"  [created] {prod['Name']}")

        # Ensure pricebook entry
        pbe = sf.query(
            f"SELECT Id FROM PricebookEntry WHERE Product2Id = '{pid}' "
            f"AND Pricebook2Id = '{pricebook_id}' LIMIT 1"
        )
        if not pbe["records"]:
            sf.PricebookEntry.create({
                "Pricebook2Id": pricebook_id,
                "Product2Id": pid,
                "UnitPrice": price,
                "IsActive": True,
            })
            print(f"    PBE created @ ${price}")

        results.append((pid, price))
    return results


def seed_orders(sf, accounts, pricebook_id):
    """Create orders with line items."""
    print("\n--- Orders ---")
    pbe_result = sf.query(
        f"SELECT Id, Product2Id, UnitPrice FROM PricebookEntry "
        f"WHERE Pricebook2Id = '{pricebook_id}' AND IsActive = true"
    )
    pbe_list = pbe_result["records"]
    if not pbe_list:
        print("  [skip] No pricebook entries found")
        return []

    descriptions = [
        "Annual license renewal", "New infrastructure setup",
        "Security compliance upgrade", "Q2 expansion order",
        "Emergency capacity increase", "Platform migration package",
        "New department onboarding", "Disaster recovery setup",
    ]

    order_ids = []
    for i in range(15):
        acct_idx = i % len(accounts)
        acct_id, acct_data = accounts[acct_idx]
        days_ago = random.randint(1, 90)
        effective_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        status = "Activated" if i % 2 == 0 else "Draft"

        try:
            order_result = sf.Order.create({
                "AccountId": acct_id,
                "Pricebook2Id": pricebook_id,
                "EffectiveDate": effective_date,
                "Status": "Draft",
                "Description": descriptions[i % len(descriptions)],
                "ShippingStreet": acct_data["BillingStreet"],
                "ShippingCity": acct_data["BillingCity"],
                "ShippingStateCode": acct_data["BillingStateCode"],
                "ShippingPostalCode": acct_data["BillingPostalCode"],
                "ShippingCountryCode": "US",
            })
            oid = order_result["id"]

            # Add 1-3 line items
            for pbe in random.sample(pbe_list, min(random.randint(1, 3), len(pbe_list))):
                sf.OrderItem.create({
                    "OrderId": oid,
                    "PricebookEntryId": pbe["Id"],
                    "Quantity": random.randint(1, 5),
                    "UnitPrice": pbe["UnitPrice"],
                })

            if status == "Activated":
                try:
                    sf.Order.update(oid, {"Status": "Activated"})
                except Exception:
                    status = "Draft"

            detail = sf.query(f"SELECT OrderNumber FROM Order WHERE Id = '{oid}' LIMIT 1")
            num = detail["records"][0]["OrderNumber"] if detail["records"] else "?"
            print(f"  [created] Order #{num} ({status})")
            order_ids.append(oid)

        except Exception as e:
            print(f"  [error] Order {i+1}: {e}")

    return order_ids


def seed_cases(sf, accounts):
    """Create support cases."""
    print("\n--- Cases ---")
    cases_data = [
        {"Subject": "Order not received - 2 weeks overdue", "Priority": "High",
         "Description": "Customer reports order placed 2 weeks ago has not arrived."},
        {"Subject": "Wrong items shipped", "Priority": "High",
         "Description": "Customer received Enterprise Server License instead of Cloud Storage."},
        {"Subject": "Request for bulk discount", "Priority": "Medium",
         "Description": "Customer interested in 50+ licenses, asking about volume pricing."},
        {"Subject": "Invoice discrepancy", "Priority": "Medium",
         "Description": "Invoice amount doesn't match agreed pricing."},
        {"Subject": "Cancel order - changed requirements", "Priority": "Low",
         "Description": "Customer's project scope changed."},
        {"Subject": "Delivery address change request", "Priority": "Medium",
         "Description": "Customer relocated office. Needs shipping address updated."},
        {"Subject": "Product compatibility question", "Priority": "Low",
         "Description": "Is API Gateway Pro compatible with Security Suite?"},
        {"Subject": "Urgent: Production system down", "Priority": "High",
         "Description": "Production environment outages. Gold support customer."},
    ]

    case_ids = []
    for i, case in enumerate(cases_data):
        acct_idx = i % len(accounts)
        case["AccountId"] = accounts[acct_idx][0]
        case["Status"] = "New"
        case["Origin"] = "Phone"
        try:
            r = sf.Case.create(case)
            detail = sf.query(f"SELECT CaseNumber FROM Case WHERE Id = '{r['id']}' LIMIT 1")
            num = detail["records"][0]["CaseNumber"] if detail["records"] else "?"
            print(f"  [created] Case #{num} - {case['Subject'][:50]}...")
            case_ids.append(r["id"])
        except Exception as e:
            print(f"  [error] Case: {e}")
    return case_ids


def seed_leads(sf):
    """Create demo leads with various statuses."""
    print("\n--- Leads ---")
    leads_data = [
        {"FirstName": "Alice", "LastName": "Chen", "Company": "TechFlow Inc",
         "Phone": "5552001001", "Email": "alice.chen@techflow.com",
         "Status": "Open - Not Contacted", "LeadSource": "Web"},
        {"FirstName": "Robert", "LastName": "Kim", "Company": "DataBridge Systems",
         "Phone": "5552002001", "Email": "r.kim@databridge.io",
         "Status": "Open - Not Contacted", "LeadSource": "Phone Inquiry"},
        {"FirstName": "Maria", "LastName": "Garcia", "Company": "CloudNine Solutions",
         "Phone": "5552003001", "Email": "maria@cloudnine.com",
         "Status": "Working - Contacted", "LeadSource": "Trade Show"},
        {"FirstName": "James", "LastName": "Wilson", "Company": "SecureNet Corp",
         "Phone": "5552004001", "Email": "jwilson@securenet.com",
         "Status": "Working - Contacted", "LeadSource": "Referral"},
        {"FirstName": "Priya", "LastName": "Patel", "Company": "InnovateTech Labs",
         "Phone": "5552005001", "Email": "priya@innovatetech.com",
         "Status": "Open - Not Contacted", "LeadSource": "Web"},
        {"FirstName": "Tom", "LastName": "Anderson", "Company": "NetVault Security",
         "Phone": "5552006001", "Email": "tom@netvault.com",
         "Status": "Working - Contacted", "LeadSource": "Phone Inquiry"},
        {"FirstName": "Lisa", "LastName": "Zhang", "Company": "QuantumLeap AI",
         "Phone": "5552007001", "Email": "lisa@quantumleap.ai",
         "Status": "Open - Not Contacted", "LeadSource": "Partner"},
        {"FirstName": "David", "LastName": "Brown", "Company": "PipelineForce",
         "Phone": "5552008001", "Email": "dbrown@pipelineforce.com",
         "Status": "Open - Not Contacted", "LeadSource": "Web"},
        {"FirstName": "Emma", "LastName": "Taylor", "Company": "GreenGrid Energy",
         "Phone": "5552009001", "Email": "emma@greengrid.com",
         "Status": "Working - Contacted", "LeadSource": "Trade Show"},
        {"FirstName": "Chris", "LastName": "Lee", "Company": "ByteShift Technologies",
         "Phone": "5552010001", "Email": "chris.lee@byteshift.com",
         "Status": "Open - Not Contacted", "LeadSource": "Referral"},
        {"FirstName": "Sophia", "LastName": "Miller", "Company": "Apex Dynamics",
         "Phone": "5552011001", "Email": "sophia@apexdyn.com",
         "Status": "Closed - Not Converted", "LeadSource": "Web"},
        {"FirstName": "Ryan", "LastName": "Clark", "Company": "FrostByte Computing",
         "Phone": "5552012001", "Email": "ryan@frostbyte.com",
         "Status": "Open - Not Contacted", "LeadSource": "Phone Inquiry"},
    ]

    lead_ids = []
    for lead in leads_data:
        existing = sf.query(f"SELECT Id FROM Lead WHERE Email = '{escape_soql(lead['Email'])}' LIMIT 1")
        if existing["records"]:
            lid = existing["records"][0]["Id"]
            print(f"  [exists] {lead['FirstName']} {lead['LastName']} ({lead['Company']})")
        else:
            try:
                r = sf.Lead.create(lead)
                lid = r["id"]
                print(f"  [created] {lead['FirstName']} {lead['LastName']} ({lead['Company']}) [{lead['Status']}]")
            except Exception as e:
                print(f"  [error] {lead['FirstName']} {lead['LastName']}: {e}")
                if "INSUFFICIENT_ACCESS" in str(e):
                    print("  >>> User needs Lead permissions. See docs/agentforce-feature-parity.md")
                    return []
                continue
        lead_ids.append(lid)
    return lead_ids


def seed_opportunities(sf, accounts, pricebook_id):
    """Create opportunities with line items."""
    print("\n--- Opportunities ---")

    pbe_result = sf.query(
        f"SELECT Id, Product2.Name, UnitPrice FROM PricebookEntry "
        f"WHERE Pricebook2Id = '{pricebook_id}' AND IsActive = true"
    )
    pbe_list = pbe_result["records"]

    stages = [
        "Prospecting", "Qualification", "Needs Analysis",
        "Proposal/Price Quote", "Negotiation/Review", "Closed Won", "Closed Lost",
    ]

    opps_data = [
        {"Name": "Acme - Enterprise Expansion", "AccountIdx": 0, "Stage": "Negotiation/Review",
         "Amount": 75000, "DaysToClose": 30, "Probability": 80},
        {"Name": "Acme - Security Upgrade", "AccountIdx": 0, "Stage": "Qualification",
         "Amount": 25000, "DaysToClose": 60, "Probability": 40},
        {"Name": "Globex - Cloud Migration", "AccountIdx": 1, "Stage": "Proposal/Price Quote",
         "Amount": 120000, "DaysToClose": 45, "Probability": 60},
        {"Name": "Globex - Support Renewal", "AccountIdx": 1, "Stage": "Closed Won",
         "Amount": 15000, "DaysToClose": -10, "Probability": 100},
        {"Name": "Initech - Platform Modernization", "AccountIdx": 2, "Stage": "Needs Analysis",
         "Amount": 200000, "DaysToClose": 90, "Probability": 30},
        {"Name": "Initech - Training Program", "AccountIdx": 2, "Stage": "Prospecting",
         "Amount": 30000, "DaysToClose": 120, "Probability": 10},
        {"Name": "Wayne - Data Center Build", "AccountIdx": 3, "Stage": "Proposal/Price Quote",
         "Amount": 350000, "DaysToClose": 60, "Probability": 50},
        {"Name": "Wayne - Compliance Suite", "AccountIdx": 3, "Stage": "Negotiation/Review",
         "Amount": 45000, "DaysToClose": 20, "Probability": 75},
        {"Name": "Stark - API Infrastructure", "AccountIdx": 4, "Stage": "Qualification",
         "Amount": 80000, "DaysToClose": 75, "Probability": 25},
        {"Name": "Stark - DevOps Transformation", "AccountIdx": 4, "Stage": "Closed Lost",
         "Amount": 60000, "DaysToClose": -30, "Probability": 0},
        {"Name": "Acme - Analytics Rollout", "AccountIdx": 0, "Stage": "Prospecting",
         "Amount": 18000, "DaysToClose": 90, "Probability": 15},
        {"Name": "Globex - Integration Project", "AccountIdx": 1, "Stage": "Needs Analysis",
         "Amount": 95000, "DaysToClose": 60, "Probability": 35},
    ]

    opp_ids = []
    for opp in opps_data:
        acct_idx = opp.pop("AccountIdx")
        acct_id = accounts[acct_idx][0]
        days = opp.pop("DaysToClose")
        close_date = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        prob = opp.pop("Probability")
        amount = opp.pop("Amount")
        stage = opp.pop("Stage")

        existing = sf.query(
            f"SELECT Id FROM Opportunity WHERE Name = '{escape_soql(opp['Name'])}' LIMIT 1"
        )
        if existing["records"]:
            oid = existing["records"][0]["Id"]
            print(f"  [exists] {opp['Name']}")
            opp_ids.append(oid)
            continue

        try:
            r = sf.Opportunity.create({
                **opp,
                "AccountId": acct_id,
                "StageName": stage,
                "CloseDate": close_date,
                "Amount": amount,
                "Probability": prob,
                "Pricebook2Id": pricebook_id,
            })
            oid = r["id"]
            print(f"  [created] {opp['Name']} ({stage}) - ${amount:,}")

            # Add 1-2 line items
            if pbe_list:
                for pbe in random.sample(pbe_list, min(random.randint(1, 2), len(pbe_list))):
                    try:
                        sf.OpportunityLineItem.create({
                            "OpportunityId": oid,
                            "PricebookEntryId": pbe["Id"],
                            "Quantity": random.randint(1, 5),
                            "UnitPrice": pbe["UnitPrice"],
                        })
                    except Exception:
                        pass

            opp_ids.append(oid)
        except Exception as e:
            print(f"  [error] {opp['Name']}: {e}")
            if "INSUFFICIENT_ACCESS" in str(e):
                print("  >>> User needs Opportunity permissions. See docs/agentforce-feature-parity.md")
                return opp_ids

    return opp_ids


def seed_tasks(sf, accounts, contacts):
    """Create tasks linked to accounts."""
    print("\n--- Tasks ---")
    tasks_data = [
        {"Subject": "Follow up on Q2 renewal", "Priority": "High", "Status": "Not Started", "DaysOut": 3, "AccountIdx": 0},
        {"Subject": "Send pricing proposal", "Priority": "Normal", "Status": "Not Started", "DaysOut": 5, "AccountIdx": 1},
        {"Subject": "Schedule product demo", "Priority": "Normal", "Status": "Not Started", "DaysOut": 7, "AccountIdx": 2},
        {"Subject": "Review contract terms", "Priority": "High", "Status": "In Progress", "DaysOut": 2, "AccountIdx": 3},
        {"Subject": "Prepare executive summary", "Priority": "Normal", "Status": "Not Started", "DaysOut": 10, "AccountIdx": 4},
        {"Subject": "Complete security audit", "Priority": "High", "Status": "In Progress", "DaysOut": 1, "AccountIdx": 0},
        {"Subject": "Update CRM records", "Priority": "Low", "Status": "Not Started", "DaysOut": 14, "AccountIdx": 1},
        {"Subject": "Call back about support issue", "Priority": "High", "Status": "Not Started", "DaysOut": 0, "AccountIdx": 2},
        {"Subject": "Send welcome package", "Priority": "Normal", "Status": "Completed", "DaysOut": -5, "AccountIdx": 3},
        {"Subject": "File quarterly report", "Priority": "Normal", "Status": "Completed", "DaysOut": -10, "AccountIdx": 4},
        {"Subject": "Onboard new contact", "Priority": "Normal", "Status": "Not Started", "DaysOut": 4, "AccountIdx": 0},
        {"Subject": "Verify shipping address", "Priority": "Normal", "Status": "Not Started", "DaysOut": 2, "AccountIdx": 1},
        {"Subject": "Prepare training materials", "Priority": "Low", "Status": "Not Started", "DaysOut": 21, "AccountIdx": 2},
        {"Subject": "Review escalated case", "Priority": "High", "Status": "In Progress", "DaysOut": 0, "AccountIdx": 3},
        {"Subject": "Send invoice reminder", "Priority": "Normal", "Status": "Completed", "DaysOut": -3, "AccountIdx": 4},
        {"Subject": "Schedule architecture review", "Priority": "Normal", "Status": "Not Started", "DaysOut": 8, "AccountIdx": 0},
        {"Subject": "Follow up on RFP submission", "Priority": "High", "Status": "Not Started", "DaysOut": 5, "AccountIdx": 1},
        {"Subject": "Process refund request", "Priority": "High", "Status": "In Progress", "DaysOut": 1, "AccountIdx": 2},
    ]

    task_ids = []
    for t in tasks_data:
        acct_idx = t.pop("AccountIdx")
        days_out = t.pop("DaysOut")
        due = (datetime.now() + timedelta(days=days_out)).strftime("%Y-%m-%d")

        # Find a contact for this account if available
        who_id = None
        matching_contacts = [c for c in contacts if c[1] == acct_idx]
        if matching_contacts:
            who_id = matching_contacts[0][0]

        try:
            data = {
                "WhatId": accounts[acct_idx][0],
                "Subject": t["Subject"],
                "Status": t["Status"],
                "Priority": t["Priority"],
                "ActivityDate": due,
            }
            if who_id:
                data["WhoId"] = who_id

            r = sf.Task.create(data)
            print(f"  [created] {t['Subject']} [{t['Status']}] due {due}")
            task_ids.append(r["id"])
        except Exception as e:
            print(f"  [error] {t['Subject']}: {e}")
            if "INSUFFICIENT_ACCESS" in str(e):
                print("  >>> User needs Task permissions. See docs/agentforce-feature-parity.md")
                return task_ids
    return task_ids


def seed_events(sf, accounts, contacts):
    """Create upcoming events."""
    print("\n--- Events ---")
    events_data = [
        {"Subject": "Quarterly Business Review", "AccountIdx": 0, "DaysOut": 5, "Hour": 10, "Duration": 60},
        {"Subject": "Product Roadmap Discussion", "AccountIdx": 1, "DaysOut": 3, "Hour": 14, "Duration": 45},
        {"Subject": "Support Escalation Call", "AccountIdx": 2, "DaysOut": 1, "Hour": 9, "Duration": 30},
        {"Subject": "Contract Negotiation Meeting", "AccountIdx": 3, "DaysOut": 7, "Hour": 11, "Duration": 90},
        {"Subject": "Technical Architecture Workshop", "AccountIdx": 4, "DaysOut": 10, "Hour": 13, "Duration": 120},
        {"Subject": "Invoice Review Call", "AccountIdx": 0, "DaysOut": 2, "Hour": 15, "Duration": 30},
        {"Subject": "New Feature Demo", "AccountIdx": 1, "DaysOut": 8, "Hour": 10, "Duration": 60},
        {"Subject": "Security Assessment Follow-up", "AccountIdx": 2, "DaysOut": 4, "Hour": 16, "Duration": 45},
        {"Subject": "Executive Sponsor Meeting", "AccountIdx": 3, "DaysOut": 14, "Hour": 9, "Duration": 60},
        {"Subject": "Migration Planning Session", "AccountIdx": 4, "DaysOut": 6, "Hour": 11, "Duration": 90},
    ]

    event_ids = []
    for ev in events_data:
        acct_idx = ev["AccountIdx"]
        start = datetime.now() + timedelta(days=ev["DaysOut"])
        start = start.replace(hour=ev["Hour"], minute=0, second=0, microsecond=0)
        end = start + timedelta(minutes=ev["Duration"])

        who_id = None
        matching_contacts = [c for c in contacts if c[1] == acct_idx]
        if matching_contacts:
            who_id = matching_contacts[0][0]

        try:
            data = {
                "WhatId": accounts[acct_idx][0],
                "Subject": ev["Subject"],
                "StartDateTime": start.isoformat(),
                "EndDateTime": end.isoformat(),
                "DurationInMinutes": ev["Duration"],
            }
            if who_id:
                data["WhoId"] = who_id

            r = sf.Event.create(data)
            print(f"  [created] {ev['Subject']} - {start.strftime('%b %d at %I:%M %p')}")
            event_ids.append(r["id"])
        except Exception as e:
            print(f"  [error] {ev['Subject']}: {e}")
            if "INSUFFICIENT_ACCESS" in str(e):
                print("  >>> User needs Event permissions. See docs/agentforce-feature-parity.md")
                return event_ids
    return event_ids


def seed_campaigns(sf, contacts, lead_ids):
    """Create campaigns and add members."""
    print("\n--- Campaigns ---")
    campaigns_data = [
        {"Name": "Q2 2026 Product Launch", "Type": "Email", "Status": "In Progress",
         "StartDate": (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
         "EndDate": (datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
         "IsActive": True},
        {"Name": "Enterprise Security Webinar", "Type": "Webinar", "Status": "Planned",
         "StartDate": (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d"),
         "EndDate": (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d"),
         "IsActive": True},
        {"Name": "Cloud Migration Campaign", "Type": "Direct Mail", "Status": "In Progress",
         "StartDate": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
         "EndDate": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
         "IsActive": True},
        {"Name": "Annual Customer Conference", "Type": "Conference", "Status": "Planned",
         "StartDate": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
         "EndDate": (datetime.now() + timedelta(days=62)).strftime("%Y-%m-%d"),
         "IsActive": True},
        {"Name": "Partner Referral Program", "Type": "Other", "Status": "In Progress",
         "StartDate": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
         "EndDate": (datetime.now() + timedelta(days=120)).strftime("%Y-%m-%d"),
         "IsActive": True},
    ]

    campaign_ids = []
    for camp in campaigns_data:
        existing = sf.query(f"SELECT Id FROM Campaign WHERE Name = '{escape_soql(camp['Name'])}' LIMIT 1")
        if existing["records"]:
            cid = existing["records"][0]["Id"]
            print(f"  [exists] {camp['Name']}")
        else:
            try:
                r = sf.Campaign.create(camp)
                cid = r["id"]
                print(f"  [created] {camp['Name']} ({camp['Type']})")
            except Exception as e:
                print(f"  [error] {camp['Name']}: {e}")
                if "INSUFFICIENT_ACCESS" in str(e):
                    print("  >>> User needs Campaign permissions. See docs/agentforce-feature-parity.md")
                    return campaign_ids
                continue
        campaign_ids.append(cid)

    # Add some contacts and leads as campaign members
    if campaign_ids:
        print("\n  Adding campaign members...")
        for i, cid in enumerate(campaign_ids):
            # Add 1-2 contacts
            for j in range(min(2, len(contacts))):
                contact_id = contacts[(i + j) % len(contacts)][0]
                try:
                    sf.CampaignMember.create({
                        "CampaignId": cid,
                        "ContactId": contact_id,
                        "Status": "Sent",
                    })
                except Exception:
                    pass  # Likely duplicate

            # Add 1-2 leads
            for j in range(min(2, len(lead_ids))):
                lid = lead_ids[(i + j) % len(lead_ids)]
                try:
                    sf.CampaignMember.create({
                        "CampaignId": cid,
                        "LeadId": lid,
                        "Status": "Sent",
                    })
                except Exception:
                    pass  # Likely duplicate

        print("  Members added.")

    return campaign_ids


def seed_knowledge_articles(sf):
    """Create Knowledge articles for FAQ/support."""
    print("\n--- Knowledge Articles ---")
    articles = [
        {"Title": "Getting Started with Enterprise Server License",
         "UrlName": "getting-started-enterprise-server",
         "Summary": "The Enterprise Server License provides full access to all server-side features including clustering, load balancing, and automatic failover. Installation requires a minimum of 8GB RAM and 4 CPU cores. Download the installer from the customer portal and use your license key to activate. Contact support if activation fails after 3 attempts."},
        {"Title": "Cloud Storage Setup and Configuration",
         "UrlName": "cloud-storage-setup",
         "Summary": "Cloud Storage 1TB plan includes automatic backup, versioning, and cross-region replication. To set up, navigate to Settings > Storage > Cloud Configuration. Enter your storage API key and select your preferred region. Data migration from on-premises storage can be initiated from the Migration tab. Allow 24-48 hours for initial sync."},
        {"Title": "API Gateway Rate Limits and Troubleshooting",
         "UrlName": "api-gateway-rate-limits",
         "Summary": "The API Gateway Pro plan includes 10 million requests per month. Rate limits reset on the 1st of each month. If you receive 429 errors, you have exceeded your rate limit. To increase your limit, upgrade your plan or contact sales. Common causes of timeouts include payload sizes over 10MB and downstream service latency."},
        {"Title": "Security Suite Features and Compliance",
         "UrlName": "security-suite-features",
         "Summary": "Security Suite Premium includes intrusion detection, vulnerability scanning, DDoS protection, and compliance reporting for SOC 2, HIPAA, and PCI DSS. The dashboard shows real-time threat monitoring. Compliance reports are generated monthly and can be downloaded from Reports > Compliance. Custom scanning schedules can be configured under Settings > Security."},
        {"Title": "Product Compatibility Matrix",
         "UrlName": "product-compatibility",
         "Summary": "All products are compatible with each other and can be deployed together. The API Gateway works with both the Enterprise Server and Cloud Storage. The Security Suite can protect all products simultaneously. The Analytics Dashboard integrates with all data sources. The DevOps Toolkit supports CI/CD for all server-side products."},
        {"Title": "How to Reset Your Account Password",
         "UrlName": "password-reset",
         "Summary": "To reset your password, go to the login page and click Forgot Password. Enter your email address and check your inbox for a reset link. The link expires after 24 hours. If you do not receive the email, check your spam folder or contact support. For security, passwords must be at least 12 characters with uppercase, lowercase, numbers, and symbols."},
        {"Title": "Billing and Invoice FAQ",
         "UrlName": "billing-faq",
         "Summary": "Invoices are generated on the 1st of each month and sent to the billing contact email. Payment is due within 30 days. We accept credit cards, ACH transfers, and wire transfers. For volume discounts on orders of 50 or more licenses, contact your account manager. Refunds for annual subscriptions are prorated based on remaining months."},
        {"Title": "Support Plan Comparison",
         "UrlName": "support-plan-comparison",
         "Summary": "We offer three support tiers. Standard support includes email support with 24-hour response time. Gold support adds phone support with 1-hour response time and 24/7 availability. Platinum support includes a dedicated account manager, priority escalation, and quarterly business reviews. All plans include access to the knowledge base and community forums."},
        {"Title": "Data Migration Best Practices",
         "UrlName": "data-migration-best-practices",
         "Summary": "Before migrating data, perform a full backup of your source system. Use our Data Migration Service for complex migrations involving more than 100GB of data. For smaller migrations, the built-in import tool supports CSV, JSON, and XML formats. Always run a test migration in a sandbox environment first. Schedule production migrations during off-peak hours."},
        {"Title": "Training and Certification Programs",
         "UrlName": "training-certification",
         "Summary": "Training packages are available in 5-seat and 10-seat options. Each package includes 40 hours of instructor-led training, hands-on labs, and certification exams. Self-paced online courses are available at no additional cost. Certification exams can be retaken once for free within 90 days. Group training for 20 or more seats qualifies for a 15 percent discount."},
        {"Title": "Troubleshooting Connection Timeouts",
         "UrlName": "connection-timeouts",
         "Summary": "Connection timeouts are usually caused by firewall rules, DNS issues, or network congestion. First, verify that ports 443 and 8443 are open in your firewall. Check DNS resolution with nslookup. If using a VPN, try connecting without it. For persistent issues, run a traceroute to our servers and share the results with support. Our status page shows current system health."},
        {"Title": "DevOps Toolkit CI/CD Pipeline Setup",
         "UrlName": "devops-cicd-setup",
         "Summary": "The DevOps Toolkit integrates with GitHub, GitLab, Bitbucket, and Azure DevOps. To set up a pipeline, install the DevOps agent on your build server, configure the connection in Settings > DevOps > Pipelines, and create a pipeline YAML file. Pre-built templates are available for common frameworks. Monitoring dashboards show build success rates, deployment frequency, and mean recovery time."},
    ]

    article_ids = []
    for art in articles:
        existing = sf.query(
            f"SELECT Id FROM Knowledge__kav WHERE UrlName = '{escape_soql(art['UrlName'])}' "
            f"AND PublishStatus IN ('Draft','Online') LIMIT 1"
        )
        if existing["records"]:
            print(f"  [exists] {art['Title'][:60]}...")
            article_ids.append(existing["records"][0]["Id"])
        else:
            try:
                r = sf.Knowledge__kav.create(art)
                article_ids.append(r["id"])
                # Publish the article
                try:
                    sf.restful('actions/standard/publishKnowledgeArticles', method='POST',
                               json={'inputs': [{'articleVersionIdList': [r['id']],
                                                 'pubAction': 'PUBLISH_ARTICLE'}]})
                    print(f"  [created+published] {art['Title'][:55]}...")
                except Exception:
                    print(f"  [created/draft] {art['Title'][:55]}...")
            except Exception as e:
                print(f"  [error] {art['Title'][:40]}: {str(e)[:100]}")
                if "not supported" in str(e).lower():
                    print("  >>> Knowledge not enabled. Enable in Setup > Knowledge Settings.")
                    return article_ids
    return article_ids


def seed_entitlements(sf, accounts):
    """Create entitlements linked to demo accounts."""
    print("\n--- Entitlements ---")
    entitlements_data = [
        {"Name": "Gold Support - Acme", "AccountIdx": 0, "Type": "Gold",
         "StartDate": "2026-01-01", "EndDate": "2026-12-31"},
        {"Name": "Platinum Support - Globex", "AccountIdx": 1, "Type": "Platinum",
         "StartDate": "2026-01-01", "EndDate": "2026-12-31"},
        {"Name": "Standard Support - Initech", "AccountIdx": 2, "Type": "Standard",
         "StartDate": "2026-01-01", "EndDate": "2026-12-31"},
        {"Name": "Gold Support - Wayne", "AccountIdx": 3, "Type": "Gold",
         "StartDate": "2025-06-01", "EndDate": "2026-06-01"},
        {"Name": "Platinum Support - Stark", "AccountIdx": 4, "Type": "Platinum",
         "StartDate": "2026-03-01", "EndDate": "2027-03-01"},
    ]

    ent_ids = []
    for ent in entitlements_data:
        acct_idx = ent.pop("AccountIdx")
        acct_id = accounts[acct_idx][0]
        acct_name = accounts[acct_idx][1]["Name"]
        existing = sf.query(
            f"SELECT Id FROM Entitlement WHERE Name = '{escape_soql(ent['Name'])}' LIMIT 1"
        )
        if existing["records"]:
            print(f"  [exists] {ent['Name']}")
            ent_ids.append(existing["records"][0]["Id"])
        else:
            try:
                ent["AccountId"] = acct_id
                r = sf.Entitlement.create(ent)
                print(f"  [created] {ent['Name']} ({ent['Type']})")
                ent_ids.append(r["id"])
            except Exception as e:
                print(f"  [error] {ent['Name']}: {str(e)[:100]}")
                if "not supported" in str(e).lower():
                    print("  >>> Entitlements not enabled. Enable in Setup > Entitlement Settings.")
                    return ent_ids
    return ent_ids


def seed_work_orders(sf, accounts):
    """Create work orders linked to demo accounts."""
    print("\n--- Work Orders ---")
    wos_data = [
        {"Subject": "Server hardware inspection", "AccountIdx": 0, "Priority": "Medium",
         "Description": "Annual hardware inspection and maintenance for on-premise servers."},
        {"Subject": "Network cabling upgrade", "AccountIdx": 1, "Priority": "High",
         "Description": "Replace Cat5e cabling with Cat6a in server room for 10Gbps support."},
        {"Subject": "Security camera installation", "AccountIdx": 2, "Priority": "Low",
         "Description": "Install 4 security cameras in the new office wing."},
        {"Subject": "Emergency UPS replacement", "AccountIdx": 3, "Priority": "Critical",
         "Description": "Replace failed UPS unit in primary data center. Risk of downtime."},
        {"Subject": "Firewall appliance setup", "AccountIdx": 4, "Priority": "Medium",
         "Description": "Configure and install new firewall appliance for DMZ network segment."},
    ]

    wo_ids = []
    for wo in wos_data:
        acct_idx = wo.pop("AccountIdx")
        acct_id = accounts[acct_idx][0]
        try:
            r = sf.WorkOrder.create({
                "AccountId": acct_id,
                "Subject": wo["Subject"],
                "Status": "New",
                "Priority": wo["Priority"],
                "Description": wo.get("Description", ""),
            })
            detail = sf.query(f"SELECT WorkOrderNumber FROM WorkOrder WHERE Id = '{r['id']}' LIMIT 1")
            num = detail["records"][0]["WorkOrderNumber"] if detail["records"] else "?"
            print(f"  [created] WO #{num} - {wo['Subject'][:50]}")
            wo_ids.append(r["id"])
        except Exception as e:
            print(f"  [error] {wo['Subject'][:40]}: {str(e)[:100]}")
            if "not supported" in str(e).lower():
                print("  >>> WorkOrders not enabled. Enable Field Service in Setup.")
                return wo_ids
    return wo_ids


def seed_assets(sf, accounts, products):
    """Create assets linked to accounts and products."""
    print("\n--- Assets ---")
    assets_data = [
        {"Name": "Enterprise Server License", "AccountIdx": 0, "ProductIdx": 0, "Qty": 3, "Serial": "ENT-2025-001"},
        {"Name": "Cloud Storage - 1TB", "AccountIdx": 0, "ProductIdx": 1, "Qty": 2, "Serial": "CLD-2025-001"},
        {"Name": "API Gateway Pro", "AccountIdx": 1, "ProductIdx": 2, "Qty": 1, "Serial": "API-2025-001"},
        {"Name": "Security Suite Premium", "AccountIdx": 1, "ProductIdx": 3, "Qty": 1, "Serial": "SEC-2025-001"},
        {"Name": "Analytics Dashboard", "AccountIdx": 2, "ProductIdx": 4, "Qty": 5, "Serial": "ANL-2025-001"},
        {"Name": "Support Plan - Gold", "AccountIdx": 2, "ProductIdx": 5, "Qty": 1, "Serial": None},
        {"Name": "DevOps Toolkit", "AccountIdx": 3, "ProductIdx": 6, "Qty": 2, "Serial": "DEV-2025-001"},
        {"Name": "Enterprise Server License", "AccountIdx": 4, "ProductIdx": 0, "Qty": 5, "Serial": "ENT-2025-002"},
        {"Name": "Security Suite Premium", "AccountIdx": 4, "ProductIdx": 3, "Qty": 2, "Serial": "SEC-2025-002"},
    ]

    asset_ids = []
    for a in assets_data:
        acct_id = accounts[a["AccountIdx"]][0]
        prod_id = products[a["ProductIdx"]][0] if a["ProductIdx"] < len(products) else None
        try:
            data = {
                "AccountId": acct_id,
                "Name": a["Name"],
                "Status": "Installed",
                "Quantity": a["Qty"],
                "PurchaseDate": "2025-01-15",
                "InstallDate": "2025-02-01",
            }
            if prod_id:
                data["Product2Id"] = prod_id
            if a.get("Serial"):
                data["SerialNumber"] = a["Serial"]
            r = sf.Asset.create(data)
            serial_txt = f" ({a['Serial']})" if a.get("Serial") else ""
            print(f"  [created] {a['Name']}{serial_txt} for {accounts[a['AccountIdx']][1]['Name']}")
            asset_ids.append(r["id"])
        except Exception as e:
            print(f"  [error] {a['Name']}: {str(e)[:100]}")
    return asset_ids


def main():
    print("=" * 60)
    print("Salesforce Super-Agent Data Seeder")
    print("=" * 60)

    print("\nConnecting to Salesforce...")
    sf = get_salesforce_client()
    print("Connected.")

    # Get Standard Pricebook
    pb = sf.query("SELECT Id, IsActive FROM Pricebook2 WHERE IsStandard = true LIMIT 1")
    if not pb["records"]:
        print("ERROR: No Standard Pricebook found.")
        return
    pricebook_id = pb["records"][0]["Id"]
    if not pb["records"][0]["IsActive"]:
        print("ERROR: Standard Pricebook is inactive. Activate it in Setup.")
        return

    # Seed in dependency order
    accounts = seed_accounts(sf, pricebook_id)
    contacts = seed_contacts(sf, accounts)
    products = seed_products(sf, pricebook_id)
    order_ids = seed_orders(sf, accounts, pricebook_id)
    case_ids = seed_cases(sf, accounts)
    lead_ids = seed_leads(sf)
    opp_ids = seed_opportunities(sf, accounts, pricebook_id)
    task_ids = seed_tasks(sf, accounts, contacts)
    event_ids = seed_events(sf, accounts, contacts)
    campaign_ids = seed_campaigns(sf, contacts, lead_ids)
    article_ids = seed_knowledge_articles(sf)
    ent_ids = seed_entitlements(sf, accounts)
    wo_ids = seed_work_orders(sf, accounts)
    asset_ids = seed_assets(sf, accounts, products)

    print("\n" + "=" * 60)
    print("Seeding complete!")
    print(f"  Accounts:      {len(accounts)}")
    print(f"  Contacts:      {len(contacts)}")
    print(f"  Products:      {len(products)}")
    print(f"  Orders:        {len(order_ids)}")
    print(f"  Cases:         {len(case_ids)}")
    print(f"  Leads:         {len(lead_ids)}")
    print(f"  Opportunities: {len(opp_ids)}")
    print(f"  Tasks:         {len(task_ids)}")
    print(f"  Events:        {len(event_ids)}")
    print(f"  Campaigns:     {len(campaign_ids)}")
    print(f"  Knowledge:     {len(article_ids)}")
    print(f"  Entitlements:  {len(ent_ids)}")
    print(f"  Work Orders:   {len(wo_ids)}")
    print(f"  Assets:        {len(asset_ids)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
