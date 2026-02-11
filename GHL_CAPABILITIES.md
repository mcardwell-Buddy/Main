# GoHighLevel (GHL) Capabilities for Buddy

## ✅ Connection Status: ACTIVE

**API Token:** Updated February 11, 2026  
**Location ID:** Sx0HPSELq34BoxUt5OF9  
**Active Pipeline:** Lead Management Pipeline (ID: bBRwSyvhR7PMtGDkrt80)

---

## 📋 Complete List of Buddy's GHL Functions

Buddy has **30+ integrated functions** to manage your GoHighLevel CRM. Here's what I can do:

---

### 👥 CONTACTS MANAGEMENT

#### **1. ghl_add_contact**
Add new contacts to your CRM with full details.

**What I Can Store:**
- Name (first/last)
- Email & phone
- Company name
- Tags (e.g., "hr-manager", "tech-industry")
- Custom fields (LinkedIn URL, job title, company size, etc.)
- Source tracking

**Example Use:**
```
"Add Sarah Johnson from TechCorp to GHL. Email: sarah@techcorp.com, 
VP of HR, 500 employees, tech industry. Tag as hr-manager."
```

#### **2. ghl_search_contact**
Search existing contacts by name, email, or phone.

**Example:** "Search GHL for contacts at techcorp.com"

#### **3. ghl_list_contacts**
View all contacts or filter by query.

#### **4. ghl_update_contact**
Update existing contact information.

#### **5. ghl_get_contact**
Retrieve full details for a specific contact.

#### **6. ghl_add_note**
Add research notes to a contact.

**Example:** "Add note to contact: Recently posted about talent acquisition challenges"

#### **7. ghl_bulk_import**
Import multiple contacts at once from research results.

---

### 🏷️ TAGGING SYSTEM

#### **8. ghl_add_tag_to_contact**
Apply tags to organize contacts (e.g., "decision-maker", "warm-lead").

#### **9. ghl_create_tag**
Create new tag categories for organization.

#### **10. ghl_list_tags**
View all available tags in your CRM.

---

### 💼 OPPORTUNITIES & PIPELINE

#### **11. ghl_create_opportunity**
Create deals/opportunities in your sales pipeline.

**What I Can Set:**
- Contact ID
- Deal name
- Pipeline & stage
- Monetary value
- Status (open/won/lost)

**Example:** "Create $10,000 opportunity for TechCorp HR consulting in Lead Management Pipeline"

#### **12. ghl_update_opportunity**
Update deal details (value, notes, status).

#### **13. ghl_move_opportunity_stage**
Move deals through your pipeline stages (New → Hot → Booked → Closed).

#### **14. ghl_list_pipelines**
View all your sales pipelines.

**Your Active Pipeline:** Lead Management Pipeline with 4 stages

#### **15. ghl_list_pipeline_stages**
List stages within a specific pipeline.

---

### ✅ TASKS & FOLLOW-UPS

#### **16. ghl_add_task**
Create follow-up tasks and reminders.

**What I Can Schedule:**
- Task title & description
- Due date/time
- Assigned user
- Linked to specific contact

**Example:** "Create task to follow up with Sarah about HR services on Feb 15"

---

### 💬 CONVERSATIONS (SMS/Email/Chat)

#### **17. ghl_send_sms**
Send SMS messages through GHL to contacts.

#### **18. ghl_send_email**
Send emails through GHL's system.

#### **19. ghl_list_conversations**
View all conversations (SMS/Email/Chat).

#### **20. ghl_get_conversation_messages**
Retrieve message history for a conversation.

#### **21. ghl_update_conversation**
Update conversation status or details.

---

### 📅 CALENDAR & APPOINTMENTS

#### **22. ghl_list_calendars**
View all available calendars.

#### **23. ghl_get_calendar_availability**
Check availability for scheduling.

#### **24. ghl_create_appointment**
Book appointments directly in GHL.

#### **25. ghl_update_appointment**
Modify appointment details.

#### **26. ghl_cancel_appointment**
Cancel scheduled appointments.

---

### 📱 WORKFLOWS & AUTOMATION

#### **27. ghl_list_workflows**
View all automated workflows.

#### **28. ghl_enroll_in_workflow**
Add contacts to automated sequences.

#### **29. ghl_remove_from_workflow**
Remove contacts from workflows.

#### **30. ghl_trigger_workflow**
Manually trigger workflow automations.

---

### 📄 FORMS & SURVEYS

#### **31. ghl_list_forms**
View all forms in your account.

#### **32. ghl_list_form_submissions**
Check form submission data.

#### **33. ghl_list_surveys**
View surveys.

#### **34. ghl_list_survey_submissions**
Check survey responses.

---

### 📊 CAMPAIGNS

#### **35. ghl_list_campaigns**
View all marketing campaigns.

#### **36. ghl_add_contact_to_campaign**
Add contacts to specific campaigns.

#### **37. ghl_update_campaign**
Modify campaign settings.

---

### 🔧 SYSTEM & ORGANIZATION

#### **38. ghl_list_users**
View all users in your GHL account.

#### **39. ghl_list_custom_fields**
View available custom field definitions.

#### **40. ghl_create_custom_field**
Create new custom fields for contacts.

---

## 🎯 Most Common Use Cases for Buddy

### **1. Prospect Research → CRM Adding**
"Find 10 HR managers at tech companies and add them to GHL with tags"
- Buddy searches web/LinkedIn
- Extracts contact info
- Adds to GHL with relevant tags
- Creates initial follow-up tasks

### **2. Contact Enrichment**
"Search for Michael Smith in GHL and update with LinkedIn profile"
- Searches GHL contacts
- Finds LinkedIn profile
- Updates contact with new info
- Adds research notes

### **3. Pipeline Management**
"Move TechCorp deal to Hot Leads stage and schedule follow-up"
- Finds opportunity in pipeline
- Moves to appropriate stage
- Creates follow-up task
- Logs activity

### **4. Bulk Contact Import**
"Import this list of 20 contacts from my research spreadsheet"
- Parses contact data
- Bulk imports to GHL
- Applies appropriate tags
- Creates opportunities if needed

### **5. Automated Outreach Setup**
"Add these 5 contacts to the HR Outreach workflow"
- Adds contacts to GHL
- Enrolls in specified workflow
- Sets up tracking

---

## 🔐 API Permissions & Scopes

Your GHL token has access to:
- ✅ Contacts (read/write)
- ✅ Opportunities (read/write)
- ✅ Tasks (read/write)
- ✅ Pipelines (read)
- ✅ Conversations (read/write)
- ✅ Workflows (read/execute)
- ✅ Calendars (read/write)
- ✅ Forms & Surveys (read)

---

## 💡 How to Use GHL with Buddy

### **Natural Language Commands:**
```
"Add John Doe from Acme Corp to GHL with email john@acme.com"
"Search GHL for contacts at microsoft.com"
"Create a $5000 opportunity for Acme Corp HR project"
"Move XYZ Corp deal to Hot Leads stage"
"Add note to contact: Posted about hiring challenges on LinkedIn"
"Create follow-up task for Sarah on February 20"
```

### **Multi-Step Missions:**
```
"Research 15 HR managers at 100+ employee tech companies, 
add them to GHL, tag as 'hr-manager' and 'tech-industry', 
create opportunities for each, and schedule follow-up tasks"
```

Buddy will break this into steps:
1. Web search for HR managers
2. Extract contact details
3. Bulk import to GHL
4. Apply tags
5. Create opportunities
6. Schedule tasks

---

## 📊 Your Current GHL Setup

**Pipeline Structure:**
```
Lead Management Pipeline
├── New Leads (incoming contacts)
├── Hot Leads (qualified prospects)
├── Appointment Booked (scheduled meetings)
└── 1 more stage
```

**Current Contacts:** 4+ in system
**Active Location:** Sx0HPSELq34BoxUt5OF9

---

## 🚨 Important Notes

1. **Separate from Email Tools**
   - `email_send_work` = Michael's Microsoft 365
   - `email_send_buddy` = Buddy's Yahoo
   - `ghl_send_email` = GHL platform email system
   
   Use GHL email for automated campaigns within GHL workflows.

2. **Tags for Organization**
   Create tags like: `hr-manager`, `tech-industry`, `500-employees`, `warm-lead`
   for better contact organization.

3. **Pipeline Stages**
   Understand your stages to use `ghl_move_opportunity_stage` effectively.

4. **Task Assignments**
   Tasks can be assigned to specific users in your GHL account.

5. **Workflow Automations**
   Use `ghl_enroll_in_workflow` to trigger automated sequences.

---

## 🔄 API Update History

- **Feb 11, 2026:** New token configured after migration leak
- **Status:** ✅ Active and tested
- **Version:** GHL API v2 (2021-07-28)

---

## 📚 Quick Reference Commands

```bash
# Test connection
python test_ghl_connection.py

# View this document
# Open: GHL_CAPABILITIES.md
```

---

**Last Updated:** February 11, 2026  
**Connection Status:** ✅ ACTIVE  
**Token Expiration:** Check GHL dashboard for token expiry
