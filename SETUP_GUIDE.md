# Salesforce Developer Edition Setup Guide

Step-by-step guide to get from zero to a working Salesforce org with full API access for the demo. Follow every step in order.

---

## Part 1: Create the Developer Edition Org (~10 min)

### Step 1: Sign up
1. Go to **https://developer.salesforce.com/signup**
2. Fill out the form:
   - **First Name / Last Name**: your real name
   - **Email**: use your work email (you'll verify it)
   - **Company**: your company name
   - **Username**: must be in email format but does NOT need to be a real email. Example: `yourname@sf-demo.dev` — this is your login username forever, so make it memorable
   - **Country**: your country
3. Click **Sign Me Up**
4. Check your email for a verification link, click it
5. Set your password

### Step 2: Log in and note your instance URL
1. Log in at **https://login.salesforce.com** with your new credentials
2. Once logged in, the browser URL bar will show the **Lightning UI URL**, something like:
   ```
   https://orgfarm-XXXXXX-dev-ed.develop.lightning.force.com/lightning/...
   ```
3. Your **API instance URL** is different — take the subdomain prefix and swap to `.develop.my.salesforce.com`:
   ```
   Lightning UI:  https://orgfarm-XXXXXX-dev-ed.develop.lightning.force.com
   API URL:       https://orgfarm-XXXXXX-dev-ed.develop.my.salesforce.com
   ```
4. **Save the API URL** — this is your `SALESFORCE_INSTANCE_URL`

---

## Part 2: Enable Features (~5 min)

### Orders
1. Setup (gear icon) → Quick Find → `Order Settings`
2. Make sure **Enable Orders** is checked → **Save**

### Knowledge
1. Quick Find → `Knowledge Settings`
2. Click **Enable Lightning Knowledge** (cannot be undone — that's fine)
3. Accept defaults for article types

### Entitlements
1. Quick Find → `Entitlement Settings`
2. Enable Entitlements → **Save**

### Work Orders (Field Service)
1. Quick Find → `Field Service Settings`
2. Enable Field Service → **Save**

---

## Part 3: Create the Integration User (~15 min)

### Step 3a: Create the user
1. In Setup, Quick Find → `Users`
2. Click **Users** → **New User**
3. Fill in:
   - **First Name**: `API`
   - **Last Name**: `Integration`
   - **Email**: your email
   - **Username**: something unique like `api-integrations@sf.dev`
   - **User License**: select **Salesforce Integration**
   - **Profile**: auto-sets to **Salesforce API Only System Integrations**
4. Check these boxes:
   - **Marketing User** (required for Campaign creation)
   - **Knowledge User** (required for Knowledge article access)
5. Click **Save**

### Step 3b: Change the profile (required for Task/Event access)

The API-Only profile cannot access Task or Event objects. Change it:

1. Quick Find → `Users` → click **Edit** on the API Integration user
2. Change **Profile** to **Salesforce Integration** (not the "API Only" variant)
3. **Save**

> Tasks and Events are "Activity" objects with special handling in Salesforce. The API-Only profile structurally cannot see them regardless of permission sets.

### Step 3c: Create the Permission Set
1. Quick Find → `Permission Sets` → **New**
2. Fill in:
   - **Label**: `Demo API Access`
   - **API Name**: `Demo_API_Access`
   - **License**: select **Salesforce API Integration**
3. Click **Save**

### Step 3d: Configure Object Permissions

Click **Object Settings**, then for each object below click it → **Edit** → check the listed permissions → **Save**:

| Object | Read | Create | Edit | View All |
|--------|------|--------|------|----------|
| Accounts | x | x | x | x |
| Contacts | x | x | x | x |
| Orders | x | x | x | x |
| Order Products | x | x | x | x |
| Cases | x | x | x | x |
| Products | x | x | x | x |
| Price Books | x | - | - | x |
| Price Book Entries | x | x | - | x |
| Leads | x | x | x | x |
| Opportunities | x | x | x | x |
| Campaigns | x | x | x | x |
| Assets | x | x | x | x |
| Events | x | x | x | x |

> **Note**: Tasks and Campaign Members may not appear in Object Settings. They inherit from the profile and parent objects respectively.

### Step 3e: Configure System Permissions

Still in the Permission Set, click **System Permissions** → **Edit**:

**Knowledge section** — check ALL boxes:
- Allow View Knowledge, Archive Articles, Knowledge One, Manage Articles,
  Manage Knowledge Article Import/Export, Manage Salesforce Knowledge,
  Publish Articles, Share Internal Knowledge Articles Externally,
  View Archived Articles, View Draft Articles

Click **Save**.

### Step 3f: Assign the Permission Set
1. Go back to the Permission Set → **Manage Assignments** → **Add Assignment**
2. Select the `API Integration` user
3. Click **Assign** → **Done**

---

## Part 4: Create the Connected App (~15 min)

### Step 4a: Create it
1. Quick Find → `App Manager` → **New Connected App**
2. Fill in:
   - **Connected App Name**: `SignalWire Demo`
   - **API Name**: auto-fills
   - **Contact Email**: your email
3. Under **API (Enable OAuth Settings)**:
   - Check **Enable OAuth Settings**
   - **Callback URL**: `https://localhost`
   - **Selected OAuth Scopes**: add **"Manage user data via APIs (api)"**
   - Check **Enable Client Credentials Flow** — click OK on the warning
4. Click **Save** → **Continue**

### Wait 2-10 minutes
Salesforce provisions the Connected App asynchronously. If you try immediately, you'll get errors.

### Step 4b: Get credentials
1. **App Manager** → find "SignalWire Demo" → dropdown → **View**
2. Click **Manage Consumer Details** (verify identity via email code)
3. Copy **Consumer Key** → `SALESFORCE_CLIENT_ID`
4. Copy **Consumer Secret** → `SALESFORCE_CLIENT_SECRET`

### Step 4c: Set the Run As user
1. **App Manager** → "SignalWire Demo" → dropdown → **Manage** → **Edit Policies**
2. Under **Client Credentials Flow**, click the magnifying glass next to **Run As**
3. Select the `API Integration` user → **Save**

---

## Part 5: Configure .env (~2 min)

```bash
cp .env.example .env
```

Fill in:
```
SALESFORCE_CLIENT_ID=your_consumer_key
SALESFORCE_CLIENT_SECRET=your_consumer_secret
SALESFORCE_INSTANCE_URL=https://orgfarm-XXXXXX-dev-ed.develop.my.salesforce.com
GOOGLE_MAPS_API_KEY=your_google_maps_key
```

---

## Part 6: Test and Seed (~5 min)

```bash
pip install -r requirements.txt
python test_connection.py
python seed_salesforce.py
```

### Publish Knowledge articles
The seeder creates articles in Draft status. To publish:
1. **App Launcher** (grid icon) → search **Knowledge**
2. Select all articles → **Publish**

> The API can create articles but publishing requires UI action due to Salesforce profile restrictions on the Integration user.

---

## Troubleshooting

### "invalid_client_id" or "invalid_client"
Wait 10 minutes after creating the Connected App. Double-check the Consumer Key.

### "invalid_grant"
The "Run As" user isn't set. App Manager → Manage → Edit Policies → set Run As.

### "INSUFFICIENT_ACCESS" on API calls
Permission Set is missing object access. Go back to Part 3d.

### "sObject type 'Task' is not supported"
The Integration user is on the wrong profile. Change to "Salesforce Integration" (Part 3b).

### "sObject type 'Knowledge__kav' is not supported"
Knowledge isn't enabled (Part 2) or the user doesn't have "Knowledge User" checked (Part 3a).

### "entity type cannot be inserted: Campaign"
The Integration user doesn't have "Marketing User" checked (Part 3a).

### "CANNOT_INSERT_UPDATE_ACTIVATE_ENTITY: Task"
An Apex trigger or Flow is blocking Task creation. Deactivate blocking Flows in Setup → Flows.

### RPC error -32603 on all tests
The AI model name is wrong. Use `gpt-4o-mini` or `gpt-4.1-mini` (not `gpt-4.1`).

---

## Estimated Total Time

| Step | Time |
|------|------|
| Sign up for org | 5 min |
| Enable features (Orders, Knowledge, Entitlements, Work Orders) | 5 min |
| Create integration user + permissions | 15 min |
| Create Connected App + wait | 15 min |
| Configure .env | 2 min |
| Test + seed | 5 min |
| **Total** | **~45 min** |

The Permission Set (Part 3d-3e) is the most tedious part — lots of clicking. Everything else is quick.
