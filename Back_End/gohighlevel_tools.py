"""
GoHighLevel Tools for Buddy

These tools allow Buddy to add contacts, create opportunities, and manage your CRM.
"""

import Back_End.gohighlevel_client as ghl_module


def ghl_add_contact(contact_info: str) -> dict:
    """
    Add a contact to GoHighLevel CRM.
    
    Args:
        contact_info: JSON string with contact details
        
    Example:
        {
            "firstName": "Sarah",
            "lastName": "Johnson", 
            "email": "sarah.j@techcorp.com",
            "phone": "+1-555-0123",
            "companyName": "TechCorp Inc",
            "tags": ["hr-manager", "tech-industry", "500-employees"],
            "customFields": {
                "linkedin_url": "https://linkedin.com/in/sarahjohnson",
                "job_title": "VP of HR",
                "company_size": "500",
                "industry": "Technology"
            },
            "source": "Buddy AI Research"
        }
    """
    import json
    
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    
    try:
        contact_data = json.loads(contact_info) if isinstance(contact_info, str) else contact_info
        result = ghl_module.ghl_client.add_contact(contact_data)
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Added {contact_data.get('firstName', '')} {contact_data.get('lastName', '')} to CRM",
                "contact_id": result["contact_id"]
            }
        else:
            return {"status": "error", "message": result.get("error")}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def ghl_update_contact(contact_id: str, updates: str) -> dict:
    import json
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    try:
        updates_data = json.loads(updates) if isinstance(updates, str) else updates
        result = ghl_module.ghl_client.update_contact(contact_id, updates_data)
        return {"status": "success"} if result.get("success") else {"status": "error", "message": result.get("error")}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def ghl_get_contact(contact_id: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.get_contact(contact_id)


def ghl_list_contacts(query: str = "", limit: int = 50, offset: int = 0) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_contacts(query=query or None, limit=limit, offset=offset)


def ghl_search_contact(query: str) -> dict:
    """
    Search for existing contacts in GoHighLevel.
    
    Args:
        query: Email, phone, or name to search for
        
    Returns:
        List of matching contacts
    """
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    
    result = ghl_module.ghl_client.search_contacts(query)
    
    if result["success"]:
        return {
            "status": "success",
            "count": result["count"],
            "contacts": result["contacts"]
        }
    else:
        return {"status": "error", "message": result.get("error")}


def ghl_add_tag_to_contact(contact_id: str, tag: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    result = ghl_module.ghl_client.add_tag_to_contact(contact_id, tag)
    return {"status": "success"} if result.get("success") else {"status": "error", "message": result.get("error")}


def ghl_list_tags() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_tags()


def ghl_create_tag(name: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.create_tag(name)


def ghl_create_opportunity(opportunity_info: str) -> dict:
    """
    Create a new opportunity/deal in GHL pipeline.
    
    Args:
        opportunity_info: JSON string with opportunity details
        
    Example:
        {
            "contactId": "contact_123abc",
            "name": "TechCorp - HR Consulting Services",
            "pipelineId": "your_pipeline_id",
            "pipelineStageId": "your_stage_id",
            "status": "open",
            "monetaryValue": 10000
        }
    """
    import json
    
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    
    try:
        opp_data = json.loads(opportunity_info) if isinstance(opportunity_info, str) else opportunity_info
        result = ghl_module.ghl_client.create_opportunity(opp_data)
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Created opportunity: {opp_data.get('name')}",
                "opportunity_id": result["opportunity_id"]
            }
        else:
            return {"status": "error", "message": result.get("error")}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def ghl_update_opportunity(opportunity_id: str, updates: str) -> dict:
    import json
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    try:
        updates_data = json.loads(updates) if isinstance(updates, str) else updates
        return ghl_module.ghl_client.update_opportunity(opportunity_id, updates_data)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def ghl_move_opportunity_stage(opportunity_id: str, pipeline_stage_id: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.move_opportunity_stage(opportunity_id, pipeline_stage_id)


def ghl_list_pipelines() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_pipelines()


def ghl_list_pipeline_stages(pipeline_id: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_pipeline_stages(pipeline_id)


def ghl_add_task(task_info: str) -> dict:
    """
    Create a follow-up task for a contact.
    
    Args:
        task_info: JSON string with task details
        
    Example:
        {
            "contactId": "contact_123abc",
            "title": "Follow up about HR services",
            "body": "Send personalized message discussing their talent acquisition needs",
            "dueDate": "2026-02-10T14:00:00Z"
        }
    """
    import json
    
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    
    try:
        task_data = json.loads(task_info) if isinstance(task_info, str) else task_info
        result = ghl_module.ghl_client.create_task(task_data)
        
        if result["success"]:
            return {
                "status": "success",
                "message": f"Created task: {task_data.get('title')}",
                "task_id": result["task_id"]
            }
        else:
            return {"status": "error", "message": result.get("error")}
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


def ghl_add_note(contact_id: str, note_text: str) -> dict:
    """
    Add a research note to a contact.
    
    Args:
        contact_id: GHL contact ID
        note_text: The note content
        
    Example:
        contact_id: "contact_123abc"
        note_text: "Research findings: VP of HR at 500-person tech company. 
                   Recently posted about talent acquisition challenges. 
                   LinkedIn shows 10+ years HR experience."
    """
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    
    result = ghl_module.ghl_client.add_note(contact_id, note_text)
    
    if result["success"]:
        return {"status": "success", "message": "Note added successfully"}
    else:
        return {"status": "error", "message": result.get("error")}


def ghl_bulk_import(contacts_json: str) -> dict:
    """
    Import multiple contacts at once from research results.
    
    Args:
        contacts_json: JSON array of contact objects
        
    Example:
        [
            {"firstName": "John", "lastName": "Smith", "email": "john@company.com", ...},
            {"firstName": "Jane", "lastName": "Doe", "email": "jane@corp.com", ...}
        ]
    """
    import json
    
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    
    try:
        contacts = json.loads(contacts_json) if isinstance(contacts_json, str) else contacts_json
        result = ghl_module.ghl_client.bulk_import_contacts(contacts)
        
        return {
            "status": "success",
            "imported": result["success"],
            "failed": result["failed"],
            "contact_ids": result["contact_ids"],
            "errors": result["errors"][:5]  # First 5 errors only
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Conversations (SMS/Email/Chat)
def ghl_list_conversations(status: str = "", limit: int = 50, offset: int = 0) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_conversations(status=status or None, limit=limit, offset=offset)


def ghl_get_conversation_messages(conversation_id: str, limit: int = 50) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.get_conversation_messages(conversation_id, limit=limit)


def ghl_send_sms(contact_id: str, message: str, conversation_id: str = None) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.send_message(contact_id, message, msg_type="SMS", conversation_id=conversation_id)


def ghl_send_email(contact_id: str, subject: str, message: str, conversation_id: str = None) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.send_message(contact_id, message, msg_type="Email", subject=subject, conversation_id=conversation_id)


def ghl_update_conversation(conversation_id: str, updates: str) -> dict:
    import json
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    try:
        updates_data = json.loads(updates) if isinstance(updates, str) else updates
        return ghl_module.ghl_client.update_conversation(conversation_id, updates_data)
    except Exception as e:
        return {"status": "error", "message": str(e)}


# Calendars & appointments
def ghl_list_calendars() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_calendars()


def ghl_get_calendar_availability(calendar_id: str, start: str, end: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.get_calendar_availability(calendar_id, start, end)


def ghl_create_appointment(appointment_info: str) -> dict:
    import json
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    try:
        appointment_data = json.loads(appointment_info) if isinstance(appointment_info, str) else appointment_info
        return ghl_module.ghl_client.create_appointment(appointment_data)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def ghl_update_appointment(appointment_id: str, updates: str) -> dict:
    import json
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    try:
        updates_data = json.loads(updates) if isinstance(updates, str) else updates
        return ghl_module.ghl_client.update_appointment(appointment_id, updates_data)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def ghl_cancel_appointment(appointment_id: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.cancel_appointment(appointment_id)


# Workflows
def ghl_list_workflows() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_workflows()


def ghl_enroll_in_workflow(workflow_id: str, contact_id: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.enroll_in_workflow(workflow_id, contact_id)


def ghl_remove_from_workflow(workflow_id: str, enrollment_id: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.remove_from_workflow(workflow_id, enrollment_id)


def ghl_trigger_workflow(workflow_id: str, payload: str) -> dict:
    import json
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    data = json.loads(payload) if isinstance(payload, str) else payload
    return ghl_module.ghl_client.trigger_workflow(workflow_id, data)


# Forms & surveys
def ghl_list_forms() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_forms()


def ghl_list_form_submissions(form_id: str = "", limit: int = 50) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_form_submissions(form_id=form_id or None, limit=limit)


def ghl_list_surveys() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_surveys()


def ghl_list_survey_submissions(survey_id: str = "", limit: int = 50) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_survey_submissions(survey_id=survey_id or None, limit=limit)


# Funnels & pages
def ghl_list_funnels() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_funnels()


def ghl_list_funnel_pages(funnel_id: str = "") -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_funnel_pages(funnel_id=funnel_id or None)


# Campaigns
def ghl_list_campaigns() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_campaigns()


def ghl_add_contact_to_campaign(campaign_id: str, contact_id: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.add_contact_to_campaign(campaign_id, contact_id)


def ghl_update_campaign(campaign_id: str, updates: str) -> dict:
    import json
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    updates_data = json.loads(updates) if isinstance(updates, str) else updates
    return ghl_module.ghl_client.update_campaign(campaign_id, updates_data)


# Users & locations
def ghl_list_users() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_users()


def ghl_list_locations() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_locations()


# Custom fields
def ghl_list_custom_fields() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_custom_fields()


def ghl_create_custom_field(field_info: str) -> dict:
    import json
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    field_data = json.loads(field_info) if isinstance(field_info, str) else field_info
    return ghl_module.ghl_client.create_custom_field(field_data)


# Webhooks
def ghl_list_webhooks() -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.list_webhooks()


def ghl_create_webhook(webhook_info: str) -> dict:
    import json
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    webhook_data = json.loads(webhook_info) if isinstance(webhook_info, str) else webhook_info
    return ghl_module.ghl_client.create_webhook(webhook_data)


def ghl_delete_webhook(webhook_id: str) -> dict:
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    return ghl_module.ghl_client.delete_webhook(webhook_id)


def ghl_request(method: str, path: str, params: str = "", data: str = "") -> dict:
    """Generic GHL request. Use for endpoints not wrapped yet."""
    import json
    if not ghl_module.ghl_client:
        return {"error": "GoHighLevel not initialized. Please set your API token."}
    params_data = json.loads(params) if isinstance(params, str) and params else None
    data_data = json.loads(data) if isinstance(data, str) and data else None
    return ghl_module.ghl_client._request(method, path, params=params_data, data=data_data)


def register_gohighlevel_tools(registry):
    """Register all GHL tools with the tool registry"""
    
    registry.register(
        "ghl_add_contact",
        ghl_add_contact,
        description="Add a new contact to GoHighLevel CRM with details from research"
    )

    registry.register(
        "ghl_update_contact",
        ghl_update_contact,
        description="Update an existing contact in GoHighLevel"
    )

    registry.register(
        "ghl_get_contact",
        ghl_get_contact,
        description="Get contact details from GoHighLevel"
    )

    registry.register(
        "ghl_list_contacts",
        ghl_list_contacts,
        description="List/search contacts in GoHighLevel"
    )
    
    registry.register(
        "ghl_search_contact",
        ghl_search_contact,
        description="Search for existing contacts in GHL to avoid duplicates"
    )

    registry.register(
        "ghl_add_tag_to_contact",
        ghl_add_tag_to_contact,
        description="Add a tag to a contact"
    )

    registry.register(
        "ghl_list_tags",
        ghl_list_tags,
        description="List all tags"
    )

    registry.register(
        "ghl_create_tag",
        ghl_create_tag,
        description="Create a new tag"
    )
    
    registry.register(
        "ghl_create_opportunity",
        ghl_create_opportunity,
        description="Create a sales opportunity for a contact"
    )

    registry.register(
        "ghl_update_opportunity",
        ghl_update_opportunity,
        description="Update an opportunity/deal"
    )

    registry.register(
        "ghl_move_opportunity_stage",
        ghl_move_opportunity_stage,
        description="Move opportunity to another pipeline stage"
    )

    registry.register(
        "ghl_list_pipelines",
        ghl_list_pipelines,
        description="List pipelines"
    )

    registry.register(
        "ghl_list_pipeline_stages",
        ghl_list_pipeline_stages,
        description="List stages for a pipeline"
    )
    
    registry.register(
        "ghl_add_task",
        ghl_add_task,
        description="Create a follow-up task for personalized outreach"
    )
    
    registry.register(
        "ghl_add_note",
        ghl_add_note,
        description="Add research notes/findings to a contact"
    )
    
    registry.register(
        "ghl_bulk_import",
        ghl_bulk_import,
        description="Import multiple contacts from research batch"
    )

    registry.register(
        "ghl_list_conversations",
        ghl_list_conversations,
        description="List conversations (SMS/Email/Chat)"
    )

    registry.register(
        "ghl_get_conversation_messages",
        ghl_get_conversation_messages,
        description="Get messages for a conversation"
    )

    registry.register(
        "ghl_send_sms",
        ghl_send_sms,
        description="Send an SMS to a contact"
    )

    registry.register(
        "ghl_send_email",
        ghl_send_email,
        description="Send an email to a contact"
    )

    registry.register(
        "ghl_update_conversation",
        ghl_update_conversation,
        description="Update conversation status/assignment"
    )

    registry.register(
        "ghl_list_calendars",
        ghl_list_calendars,
        description="List calendars"
    )

    registry.register(
        "ghl_get_calendar_availability",
        ghl_get_calendar_availability,
        description="Get calendar availability"
    )

    registry.register(
        "ghl_create_appointment",
        ghl_create_appointment,
        description="Create appointment"
    )

    registry.register(
        "ghl_update_appointment",
        ghl_update_appointment,
        description="Reschedule/update appointment"
    )

    registry.register(
        "ghl_cancel_appointment",
        ghl_cancel_appointment,
        description="Cancel appointment"
    )

    registry.register(
        "ghl_list_workflows",
        ghl_list_workflows,
        description="List workflows"
    )

    registry.register(
        "ghl_enroll_in_workflow",
        ghl_enroll_in_workflow,
        description="Enroll contact into workflow"
    )

    registry.register(
        "ghl_remove_from_workflow",
        ghl_remove_from_workflow,
        description="Remove contact from workflow"
    )

    registry.register(
        "ghl_trigger_workflow",
        ghl_trigger_workflow,
        description="Trigger workflow"
    )

    registry.register(
        "ghl_list_forms",
        ghl_list_forms,
        description="List forms"
    )

    registry.register(
        "ghl_list_form_submissions",
        ghl_list_form_submissions,
        description="List form submissions"
    )

    registry.register(
        "ghl_list_surveys",
        ghl_list_surveys,
        description="List surveys"
    )

    registry.register(
        "ghl_list_survey_submissions",
        ghl_list_survey_submissions,
        description="List survey submissions"
    )

    registry.register(
        "ghl_list_funnels",
        ghl_list_funnels,
        description="List funnels"
    )

    registry.register(
        "ghl_list_funnel_pages",
        ghl_list_funnel_pages,
        description="List funnel pages"
    )

    registry.register(
        "ghl_list_campaigns",
        ghl_list_campaigns,
        description="List campaigns"
    )

    registry.register(
        "ghl_add_contact_to_campaign",
        ghl_add_contact_to_campaign,
        description="Add contact to campaign"
    )

    registry.register(
        "ghl_update_campaign",
        ghl_update_campaign,
        description="Update campaign"
    )

    registry.register(
        "ghl_list_users",
        ghl_list_users,
        description="List users"
    )

    registry.register(
        "ghl_list_locations",
        ghl_list_locations,
        description="List locations"
    )

    registry.register(
        "ghl_list_custom_fields",
        ghl_list_custom_fields,
        description="List custom fields"
    )

    registry.register(
        "ghl_create_custom_field",
        ghl_create_custom_field,
        description="Create custom field"
    )

    registry.register(
        "ghl_list_webhooks",
        ghl_list_webhooks,
        description="List webhooks"
    )

    registry.register(
        "ghl_create_webhook",
        ghl_create_webhook,
        description="Create webhook"
    )

    registry.register(
        "ghl_delete_webhook",
        ghl_delete_webhook,
        description="Delete webhook"
    )

    registry.register(
        "ghl_request",
        ghl_request,
        description="Generic GHL request for endpoints not wrapped"
    )

