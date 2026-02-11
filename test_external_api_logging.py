#!/usr/bin/env python3
"""
Test script to generate sample external API usage data
"""

import sys
sys.path.insert(0, '.')

from Back_End.whiteboard_metrics import log_external_api_usage

# Simulate some external API calls
print("Logging sample external API usage...")

# OpenAI calls
for i in range(5):
    log_external_api_usage(
        company="OpenAI",
        request_type="chat_completion",
        duration_ms=250 + (i * 10),
        cost_usd=0.002 + (i * 0.0001)
    )

for i in range(3):
    log_external_api_usage(
        company="OpenAI",
        request_type="text_embedding",
        duration_ms=150 + (i * 5),
        cost_usd=0.00005
    )

# SerpAPI calls
for i in range(8):
    log_external_api_usage(
        company="SerpAPI",
        request_type="google_search",
        duration_ms=500 + (i * 20),
        cost_usd=0.0000278  # Credit-based, converted to USD
    )

# GoHighLevel calls
for i in range(4):
    log_external_api_usage(
        company="GoHighLevel",
        request_type="contact_create",
        duration_ms=200 + (i * 15),
        cost_usd=0.0  # Subscription-based
    )

for i in range(2):
    log_external_api_usage(
        company="GoHighLevel",
        request_type="contact_update",
        duration_ms=180 + (i * 10),
        cost_usd=0.0
    )

# Microsoft Graph calls
for i in range(6):
    log_external_api_usage(
        company="Microsoft Graph",
        request_type="mail_send",
        duration_ms=300 + (i * 25),
        cost_usd=0.0  # Windows subscription included
    )

print("✓ Sample external API usage logged successfully!")
print("Run the Monitor page to see the External APIs section with collapsible companies.")
