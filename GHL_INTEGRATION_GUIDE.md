# GoHighLevel Integration Setup

## What This Enables

Buddy can now:
- ✅ Add contacts to your GHL CRM
- ✅ Search for existing contacts (avoid duplicates)
- ✅ Create opportunities/deals
- ✅ Add follow-up tasks
- ✅ Add research notes to contacts
- ✅ Bulk import contacts from research

## Setup Steps

### 1. Get Your GHL API Token

1. Log into GoHighLevel
2. Go to **Settings** → **API**
3. Copy your **API Key/Token**
4. (Optional) Copy your **Location ID** if you have multiple locations

### 2. Configure Buddy

Send a POST request to configure:

```bash
curl -X POST http://localhost:8000/ghl/configure \
  -H "Content-Type: application/json" \
  -d '{
    "api_token": "YOUR_GHL_API_TOKEN_HERE",
    "location_id": "YOUR_LOCATION_ID" 
  }'
```

Or use Buddy's chat:

```
You: "Configure GoHighLevel with token: [YOUR_TOKEN]"
```

### 3. Verify Connection

```bash
curl http://localhost:8000/ghl/status
```

Should return:
```json
{
  "configured": true,
  "message": "GoHighLevel is ready"
}
```

## Usage Examples

### Example 1: Research HR Manager → Add to CRM

**You ask Buddy:**
> "Find HR managers at tech companies in Austin and add them to my CRM"

**Buddy will:**
1. Search for HR managers (public data sources)
2. Cross-reference company information
3. For each person found:
   - Extract: name, title, company, email (if available), LinkedIn
   - Call `ghl_add_contact` to add to your CRM
   - Add tags: ["hr-manager", "tech-industry", "austin"]
   - Add notes with research findings

**Result in GHL:**
```
New Contact: Sarah Johnson
Email: sarah.j@techcorp.com
Company: TechCorp Inc
Title: VP of HR
Tags: hr-manager, tech-industry, austin, 500-employees
Custom Fields:
  - LinkedIn: https://linkedin.com/in/sarahjohnson
  - Company Size: 500
  - Industry: Technology
Notes: "Research findings: VP of HR at 500-person tech company..."
```

### Example 2: Bulk Import from Research

**You ask Buddy:**
> "I have a list of 20 HR contacts. Import them to GHL."

Then paste:
```
- John Smith, HR Director, Acme Corp, john@acme.com
- Jane Doe, VP People Ops, TechCo, jane@techco.com
...
```

**Buddy will:**
1. Parse the list
2. Structure data for GHL
3. Call `ghl_bulk_import` with all contacts
4. Report: "Imported 18 contacts, 2 duplicates skipped"

### Example 3: Create Opportunity + Task

**You ask Buddy:**
> "Add Sarah Johnson from TechCorp to my pipeline and create a follow-up task"

**Buddy will:**
1. Search GHL for "Sarah Johnson TechCorp"
2. Create opportunity: "TechCorp - HR Consulting"
3. Create task: "Send personalized message about talent acquisition"
4. Set due date: 2 days from now

## Available Commands

### Add Single Contact
```
"Add [Name] from [Company] to my CRM"
"Create a contact for [email] in GHL"
```

### Search Before Adding
```
"Check if [Name/Email] is already in my CRM"
"Search for contacts at [Company]"
```

### Create Opportunity
```
"Create an opportunity for [Contact] worth $[Amount]"
"Add [Contact] to my sales pipeline"
```

### Add Task
```
"Remind me to follow up with [Contact] on [Date]"
"Create a task to reach out to [Contact]"
```

### Bulk Operations
```
"Import these 50 contacts to GHL: [list]"
"Add all these people to my CRM with tag [tag-name]"
```

## What Data Gets Captured

When Buddy adds a contact from research:

**Standard Fields:**
- First Name, Last Name
- Email (if found)
- Phone (if found)
- Company Name
- Source: "Buddy AI Research"

**Custom Fields:**
- linkedin_url
- job_title
- company_size
- industry
- location

**Tags (automatic):**
- Job level (hr-manager, hr-director, vp-hr)
- Industry (tech-industry, healthcare, finance)
- Company size (startup, mid-market, enterprise)
- Location (city/region)

**Notes:**
- Where found (LinkedIn, company site, etc.)
- Key insights (recent posts, company news, etc.)
- Best approach for outreach

## Workflow Example

### Scenario: Find 50 HR Managers for Outreach

**Step 1: You ask Buddy**
```
"Find 50 HR managers at tech companies with 100-500 employees 
in Austin, Denver, or Seattle. Add them to my GHL with research notes."
```

**Step 2: Buddy executes**
1. Searches public databases
2. Filters by criteria (job title, company size, location)
3. For each match:
   - Validates company info
   - Finds email (if possible)
   - Researches recent activity
4. Adds to GHL with:
   - Contact details
   - Tags: ["hr-manager", "tech", "100-500-employees", "austin"]
   - Notes: Research findings
   - Task: "Personalized outreach" (due in 2 days)

**Step 3: You get notified**
```
✓ Added 47 contacts to GHL
✗ 3 were duplicates (skipped)
✓ Created 47 follow-up tasks
✓ Tagged all with: hr-manager, tech-industry, target-size

Next steps in your CRM:
- Review research notes
- Customize outreach messages
- Send via GHL campaigns
```

**Step 4: You follow up (manually via GHL)**
- Review the contacts in GHL
- Read Buddy's research notes
- Send personalized messages through GHL
- Track responses in your pipeline

## Security Notes

✅ **Your API token never leaves your server**
- Stored in memory only (not saved to disk)
- Used only for YOUR requests
- You can revoke it anytime in GHL settings

✅ **No automated messaging**
- Buddy only adds contacts
- YOU send messages via GHL
- Full control over outreach

✅ **Respects GHL rate limits**
- Won't spam your CRM
- Checks for duplicates before adding

## Integration with Other Tools

Buddy can combine GHL with other research:

```
"Search company websites for HR contacts, 
find their emails with Hunter.io,
research their LinkedIn activity,
and add to GHL with personalized notes"
```

This gives you:
1. Contact details in GHL
2. Email addresses verified
3. Research notes for personalization
4. Tags for segmentation
5. Tasks for follow-up timing

Then you use GHL to:
- Send personalized emails
- Track opens/clicks
- Nurture in sequences
- Convert to customers

## Troubleshooting

**"GoHighLevel not configured"**
→ Run `/ghl/configure` endpoint with your token

**"Contact already exists"**
→ Buddy will skip duplicates automatically

**"API token invalid"**
→ Check your GHL settings, generate new token

**"Missing location_id"**
→ Either provide location_id in config, or include in each contact

## Rate Limits

GHL typically allows:
- 100 requests/minute for most endpoints
- 10 contacts/second for bulk imports

Buddy respects these limits automatically.

## Next Steps

Once configured, try:
1. **Test**: "Add a test contact to my GHL"
2. **Research**: "Find 5 HR managers in tech and add them"
3. **Bulk**: "Import this CSV of contacts to GHL"
4. **Automate**: Set up workflows for ongoing research

Your token is ready. Just configure and Buddy will start populating your CRM!
