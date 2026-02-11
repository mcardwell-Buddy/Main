"""
Natural Language Response Parser & Artifact Delivery Flow

Handles user responses about artifact delivery:
- "Yes, email it to me"
- "Save it to OneDrive"
- "Both please"
- "No thanks"

Integrates with Buddy's approval flow to offer delivery options after task completion.
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path


class DeliveryIntentParser:
    """
    Parses natural language responses to determine delivery intent.
    
    Understands:
    - Affirmative: yes, sure, please, go ahead, yep, yeah
    - Negative: no, nope, skip, don't, not now
    - Email intent: email, send, mail
    - OneDrive intent: onedrive, cloud, save, upload, drive
    - Both: both, and, also
    """
    
    def __init__(self):
        from Back_End.llm_client import llm_client
        self.llm = llm_client
        
    def parse_delivery_intent(self, user_response: str) -> Dict[str, Any]:
        """
        Parse user's natural language response about delivery.
        
        Args:
            user_response: User's message like "yes email it"
            
        Returns:
            Intent dict with actions:
            {
                "wants_delivery": bool,
                "email": bool,
                "onedrive": bool,
                "custom_message": str | None,
                "confidence": float
            }
        """
        # Use LLM for robust parsing
        prompt = f"""Parse this user response about artifact delivery:

USER RESPONSE: "{user_response}"

Determine:
1. Does the user want delivery? (yes/no)
2. Do they want email delivery?
3. Do they want OneDrive delivery?
4. Did they provide a custom message?

Examples:
- "yes please email it" → wants delivery, email=true, onedrive=false
- "save to onedrive" → wants delivery, email=false, onedrive=true
- "both please" → wants delivery, email=true, onedrive=true
- "no thanks" → wants delivery=false
- "email it with a note saying this is version 2" → wants delivery, email=true, message="this is version 2"

Return JSON:
{{
    "wants_delivery": true/false,
    "email": true/false,
    "onedrive": true/false,
    "custom_message": "..." or null,
    "confidence": 0.0-1.0
}}"""
        
        try:
            response = self.llm.complete(prompt, temperature=0.2)
            
            # Extract JSON
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            
            intent = json.loads(json_str)
            
            # Validate
            if "wants_delivery" not in intent:
                intent["wants_delivery"] = False
            if "email" not in intent:
                intent["email"] = False
            if "onedrive" not in intent:
                intent["onedrive"] = False
            if "custom_message" not in intent:
                intent["custom_message"] = None
            if "confidence" not in intent:
                intent["confidence"] = 0.8
            
            return intent
            
        except Exception as e:
            print(f"❌ Error parsing delivery intent: {e}")
            # Fallback to simple keyword matching
            return self._fallback_parse(user_response)
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """Simple keyword-based fallback parser"""
        text = response.lower()
        
        # Check for negative
        negative_keywords = ['no', 'nope', 'skip', "don't", 'not', 'never']
        is_negative = any(word in text for word in negative_keywords)
        
        # Check for delivery methods
        email_keywords = ['email', 'mail', 'send']
        onedrive_keywords = ['onedrive', 'cloud', 'drive', 'save', 'upload']
        both_keywords = ['both', 'and also', 'also']
        
        has_email = any(word in text for word in email_keywords)
        has_onedrive = any(word in text for word in onedrive_keywords)
        has_both = any(word in text for word in both_keywords)
        
        # Determine intent
        if is_negative:
            wants_delivery = False
            email = False
            onedrive = False
        elif has_both:
            wants_delivery = True
            email = True
            onedrive = True
        elif has_email:
            wants_delivery = True
            email = True
            onedrive = False
        elif has_onedrive:
            wants_delivery = True
            email = False
            onedrive = True
        else:
            # Ambiguous - assume they want email if affirmative
            affirmative = ['yes', 'yeah', 'yep', 'sure', 'ok', 'please']
            wants_delivery = any(word in text for word in affirmative)
            email = wants_delivery
            onedrive = False
        
        return {
            "wants_delivery": wants_delivery,
            "email": email,
            "onedrive": onedrive,
            "custom_message": None,
            "confidence": 0.6
        }


class ArtifactDeliveryOrchestrator:
    """
    Orchestrates artifact delivery flow after task completion.
    
    Flow:
    1. Task completes → Identify artifacts created
    2. Offer delivery options to user
    3. Parse user's natural language response
    4. Execute delivery (email/OneDrive/both)
    5. Confirm delivery
    """
    
    def __init__(self):
        from Back_End.onedrive_client import get_delivery_service
        self.delivery_service = get_delivery_service()
        self.intent_parser = DeliveryIntentParser()
        self.pending_deliveries_path = Path("data/pending_deliveries.json")
        
    def offer_delivery(
        self,
        mission_id: str,
        artifacts: List[str],
        user_email: str
    ) -> Dict[str, Any]:
        """
        Create a delivery offer for completed mission artifacts.
        
        Args:
            mission_id: ID of completed mission
            artifacts: List of file paths created
            user_email: User's email address
            
        Returns:
            Offer dict with options
        """
        offer = {
            "mission_id": mission_id,
            "artifacts": artifacts,
            "user_email": user_email,
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }
        
        # Save as pending delivery
        self._save_pending_delivery(offer)
        
        # Generate offer message
        artifact_names = [Path(a).name for a in artifacts]
        
        if len(artifact_names) == 1:
            files_msg = f"**{artifact_names[0]}**"
        else:
            files_msg = "**" + "**, **".join(artifact_names[:-1]) + f"** and **{artifact_names[-1]}**"
        
        offer_message = f"""🎉 **Task Complete!**

I've built {files_msg} for you.

**Would you like me to send these to you?**

Options:
- 📧 **Email**: I'll send them as attachments
- ☁️ **OneDrive**: I'll save them to your OneDrive folder
- 🎯 **Both**: Email + OneDrive

Just reply naturally:
- "Yes, email it"
- "Save to OneDrive"
- "Both please"
- "No thanks"

What would you prefer? 😊"""
        
        return {
            "offer_id": mission_id,
            "message": offer_message,
            "artifacts": artifacts,
            "options": ["email", "onedrive", "both", "decline"]
        }
    
    def handle_delivery_response(
        self,
        mission_id: str,
        user_response: str
    ) -> Dict[str, Any]:
        """
        Process user's response to delivery offer.
        
        Args:
            mission_id: Mission ID / offer ID
            user_response: User's natural language reply
            
        Returns:
            Delivery execution result
        """
        # Parse intent
        intent = self.intent_parser.parse_delivery_intent(user_response)
        
        # Get pending delivery
        pending = self._get_pending_delivery(mission_id)
        if not pending:
            return {
                "success": False,
                "error": "No pending delivery found for this mission."
            }
        
        # Handle no delivery
        if not intent["wants_delivery"]:
            self._mark_delivery_completed(mission_id, "declined")
            return {
                "success": True,
                "action": "declined",
                "message": "No problem! The files are saved locally if you need them later. 👍"
            }
        
        # Execute deliveries
        results = []
        
        if intent["email"]:
            email_result = self._execute_email_delivery(
                pending, intent.get("custom_message")
            )
            results.append(email_result)
        
        if intent["onedrive"]:
            onedrive_result = self._execute_onedrive_delivery(
                pending, intent.get("custom_message")
            )
            results.append(onedrive_result)
        
        # Mark as completed
        self._mark_delivery_completed(mission_id, "delivered")
        
        # Generate response message
        success_count = sum(1 for r in results if r["success"])
        
        if success_count == len(results):
            status_emoji = "✅"
            status_msg = "All deliveries successful!"
        elif success_count > 0:
            status_emoji = "⚠️"
            status_msg = "Some deliveries succeeded."
        else:
            status_emoji = "❌"
            status_msg = "Delivery failed."
        
        response_parts = [f"{status_emoji} **{status_msg}**\n"]
        
        for result in results:
            if result["method"] == "email":
                if result["success"]:
                    response_parts.append("📧 Email sent successfully!")
                else:
                    response_parts.append(f"📧 Email failed: {result.get('error', 'Unknown error')}")
            
            elif result["method"] == "onedrive":
                if result["success"]:
                    web_url = result.get("upload", {}).get("web_url", "")
                    response_parts.append(f"☁️ Saved to OneDrive: [View Files]({web_url})")
                else:
                    response_parts.append(f"☁️ OneDrive failed: {result.get('error', 'Unknown error')}")
        
        return {
            "success": success_count > 0,
            "intent": intent,
            "results": results,
            "message": "\n".join(response_parts)
        }
    
    def _execute_email_delivery(
        self,
        pending_delivery: Dict[str, Any],
        custom_message: Optional[str]
    ) -> Dict[str, Any]:
        """Execute email delivery for all artifacts"""
        artifacts = pending_delivery["artifacts"]
        email = pending_delivery["user_email"]
        
        # Send all artifacts in one email
        from Back_End.email_client import get_email_client
        email_client = get_email_client()
        
        artifact_names = [Path(a).name for a in artifacts]
        subject = f"Buddy Built: {', '.join(artifact_names)}"
        
        body = custom_message or f"""Hi there! 👋

I've completed your task and built the following files:

{chr(10).join(f'📄 {name}' for name in artifact_names)}

Please find them attached to this email.

Best regards,
Buddy 🤖"""
        
        result = email_client.send_email(
            to=email,
            subject=subject,
            body=body,
            attachments=artifacts
        )
        
        result["method"] = "email"
        return result
    
    def _execute_onedrive_delivery(
        self,
        pending_delivery: Dict[str, Any],
        custom_message: Optional[str]
    ) -> Dict[str, Any]:
        """Execute OneDrive delivery for all artifacts"""
        artifacts = pending_delivery["artifacts"]
        email = pending_delivery["user_email"]
        mission_id = pending_delivery["mission_id"]
        
        # Upload each artifact
        upload_results = []
        for artifact in artifacts:
            result = self.delivery_service.onedrive_client.upload_file(
                artifact,
                onedrive_folder=f"/Buddy Artifacts/{mission_id}"
            )
            upload_results.append(result)
        
        # Check if all succeeded
        all_success = all(r["success"] for r in upload_results)
        
        if not all_success:
            failed = [r for r in upload_results if not r["success"]]
            return {
                "success": False,
                "method": "onedrive",
                "error": f"Failed to upload {len(failed)} files",
                "details": failed
            }
        
        # Send notification email
        from Back_End.email_client import get_email_client
        email_client = get_email_client()
        
        artifact_names = [Path(a).name for a in artifacts]
        web_url = upload_results[0]["web_url"].rsplit('/', 1)[0]  # Folder URL
        
        subject = f"Buddy Saved: Files to OneDrive"
        body = custom_message or f"""Hi there! 👋

I've saved your files to OneDrive:

{chr(10).join(f'📄 {name}' for name in artifact_names)}

📁 **View them here:** {web_url}

Best regards,
Buddy 🤖"""
        
        notification = email_client.send_email(
            to=email,
            subject=subject,
            body=body
        )
        
        return {
            "success": True,
            "method": "onedrive",
            "upload": upload_results[0],  # Return first for web_url
            "uploads": upload_results,
            "notification": notification
        }
    
    def _save_pending_delivery(self, offer: Dict[str, Any]):
        """Save pending delivery to storage"""
        self.pending_deliveries_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing
        if self.pending_deliveries_path.exists():
            with open(self.pending_deliveries_path, 'r') as f:
                pending = json.load(f)
        else:
            pending = {}
        
        # Add new
        pending[offer["mission_id"]] = offer
        
        # Save
        with open(self.pending_deliveries_path, 'w') as f:
            json.dump(pending, f, indent=2)
    
    def _get_pending_delivery(self, mission_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve pending delivery by mission ID"""
        if not self.pending_deliveries_path.exists():
            return None
        
        with open(self.pending_deliveries_path, 'r') as f:
            pending = json.load(f)
        
        return pending.get(mission_id)
    
    def _mark_delivery_completed(self, mission_id: str, status: str):
        """Mark delivery as completed or declined"""
        if not self.pending_deliveries_path.exists():
            return
        
        with open(self.pending_deliveries_path, 'r') as f:
            pending = json.load(f)
        
        if mission_id in pending:
            pending[mission_id]["status"] = status
            pending[mission_id]["completed_at"] = datetime.utcnow().isoformat()
        
        with open(self.pending_deliveries_path, 'w') as f:
            json.dump(pending, f, indent=2)


# Singleton
_orchestrator = None


def get_delivery_orchestrator() -> ArtifactDeliveryOrchestrator:
    """Get or create delivery orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ArtifactDeliveryOrchestrator()
    return _orchestrator

