"""
Test Salesforce connection and API access for all objects the agent uses.
Run this after setting up your .env file to verify everything works.
"""

from salesforce_client import get_salesforce_client


def main():
    print("=" * 60)
    print("Salesforce Connection Test — SF Agent Demo")
    print("=" * 60)

    # Step 1: Auth
    print("\n1. Requesting OAuth token...", end=" ")
    try:
        sf = get_salesforce_client()
        print("SUCCESS")
    except Exception as e:
        print(f"FAILED\n   Error: {e}")
        return

    # Step 2: Core objects
    objects = [
        ("Account", None),
        ("Contact", None),
        ("Order", "Make sure Orders are enabled in Setup > Order Settings"),
        ("OrderItem", None),
        ("Case", None),
        ("Lead", "Add Lead permissions to the Integration user's Permission Set"),
        ("Opportunity", "Add Opportunity permissions to the Permission Set"),
        ("Task", "Integration user may need 'Salesforce Integration' profile (not API Only)"),
        ("Event", "Same as Task — needs the Salesforce Integration profile"),
        ("Campaign", "Enable Marketing User checkbox on the Integration user"),
        ("CampaignMember", None),
        ("Asset", "Add Asset permissions to the Permission Set"),
        ("Product2", None),
        ("PricebookEntry", None),
    ]

    print(f"\n2. Testing object access ({len(objects)} objects):")
    passed = 0
    for i, (obj, hint) in enumerate(objects, 1):
        print(f"   {i:2d}. {obj:20s}", end=" ")
        try:
            result = sf.query(f"SELECT COUNT() FROM {obj}")
            count = result["totalSize"]
            print(f"OK ({count} records)")
            passed += 1
        except Exception as e:
            print(f"FAILED")
            if hint:
                print(f"       Hint: {hint}")

    # Step 3: Knowledge (may not be enabled)
    print(f"\n3. Knowledge articles...", end=" ")
    try:
        result = sf.query("SELECT COUNT() FROM Knowledge__kav")
        count = result["totalSize"]
        print(f"OK ({count} articles)")
        passed += 1

        # Check publish status
        published = sf.query(
            "SELECT COUNT() FROM Knowledge__kav WHERE PublishStatus = 'Online'"
        )
        pub_count = published["totalSize"]
        if pub_count == 0 and count > 0:
            print(f"       WARNING: {count} articles exist but none are published.")
            print(f"       Publish them: App Launcher > Knowledge > select all > Publish")
        else:
            print(f"       ({pub_count} published)")
    except Exception:
        print("NOT AVAILABLE")
        print("       Enable: Setup > Knowledge Settings > Enable Lightning Knowledge")
        print("       Then: check 'Knowledge User' on the Integration user")

    # Step 4: Entitlements (may not be enabled)
    print(f"4. Entitlements...", end=" ")
    try:
        result = sf.query("SELECT COUNT() FROM Entitlement")
        print(f"OK ({result['totalSize']} records)")
        passed += 1
    except Exception:
        print("NOT AVAILABLE")
        print("       Enable: Setup > Entitlement Settings > Enable Entitlements")

    # Step 5: Work Orders (may not be enabled)
    print(f"5. Work Orders...", end=" ")
    try:
        result = sf.query("SELECT COUNT() FROM WorkOrder")
        print(f"OK ({result['totalSize']} records)")
        passed += 1
    except Exception:
        print("NOT AVAILABLE")
        print("       Enable: Setup > Field Service Settings")

    # Step 6: Standard Pricebook
    print(f"6. Standard Pricebook...", end=" ")
    try:
        result = sf.query(
            "SELECT Id, Name, IsActive FROM Pricebook2 WHERE IsStandard = true"
        )
        if result["records"]:
            pb = result["records"][0]
            status = "Active" if pb["IsActive"] else "INACTIVE (activate in Setup > Price Books)"
            print(f"OK — {pb['Name']} ({status})")
        else:
            print("WARNING — No Standard Pricebook found")
    except Exception as e:
        print(f"FAILED — {e}")

    total = len(objects) + 3  # +3 for Knowledge, Entitlements, Work Orders
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} object types accessible")
    if passed >= len(objects):
        print("Core objects OK. Run seed_salesforce.py to populate demo data.")
    else:
        print("Some objects are missing. Check Permission Set and Setup hints above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
