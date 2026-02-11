"""
Send test emails from both accounts to verify dual email system

Author: Buddy
Date: February 11, 2026
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from Back_End.tool_email import send_work_email, send_buddy_email

print("\n" + "="*80)
print("SENDING TEST EMAILS")
print("="*80 + "\n")

# Test 1: Work Email (Michael's professional account)
print("📧 Sending work email from Michael Cardwell's professional account...")
work_result = send_work_email(
    to="michaelcardwell@yahoo.com",
    subject="Test: Professional Work Email from Buddy",
    template="notification",
    name="Michael",
    title="Work Email System Test",
    content=(
        "This is a test email from your PROFESSIONAL email account.\n\n"
        "Account Type: Microsoft 365 (Cardwell Associates)\n"
        "Authentication: Microsoft Graph API\n"
        "Purpose: Business and professional communications\n\n"
        "If you receive this email, your work email integration is working correctly!"
    )
)

if work_result['success']:
    print(f"✅ Work email sent successfully!")
    print(f"   From: {work_result.get('from', 'Microsoft 365 account')}")
    print(f"   Duration: {work_result['duration_ms']}ms\n")
else:
    print(f"❌ Work email failed: {work_result['error']}\n")

# Test 2: Buddy Personal Email (Yahoo)
print("📧 Sending Buddy's personal email from Yahoo account...")
buddy_result = send_buddy_email(
    to="michaelcardwell@yahoo.com",
    subject="Test: Buddy's Personal Email",
    template="notification",
    name="Michael",
    title="Buddy Email System Test",
    content=(
        "This is a test email from BUDDY'S PERSONAL email account.\n\n"
        "Account: buddy.cardwell@yahoo.com\n"
        "Authentication: Yahoo SMTP\n"
        "Purpose: Buddy's operational and personal communications\n\n"
        "If you receive this email, Buddy's personal email integration is working correctly!"
    )
)

if buddy_result['success']:
    print(f"✅ Buddy email sent successfully!")
    print(f"   From: {buddy_result['from']}")
    print(f"   Duration: {buddy_result['duration_ms']}ms\n")
else:
    print(f"❌ Buddy email failed: {buddy_result['error']}\n")

# Summary
print("="*80)
print("SUMMARY")
print("="*80)
print(f"Work Email (Microsoft 365): {'✅ SUCCESS' if work_result['success'] else '❌ FAILED'}")
print(f"Buddy Email (Yahoo):        {'✅ SUCCESS' if buddy_result['success'] else '❌ FAILED'}")
print("\nCheck michaelcardwell@yahoo.com for both test emails!")
print("="*80 + "\n")
