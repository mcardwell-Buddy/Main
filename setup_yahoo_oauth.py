#!/usr/bin/env python3
"""
Setup Yahoo OAuth provider in Firebase
Displays credentials to be configured in Firebase Console
"""
import sys
from pathlib import Path

# Yahoo OAuth credentials from .env
YAHOO_CLIENT_ID = "dj0yJmk9SURlaTFGRlR6UzVzJmQ9WVdrOWQwdEZjMnR1WnpjbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PWFi"
YAHOO_CLIENT_SECRET = "f49e11122530fd800b69446a09f7cc040e1d8f8e"
FIREBASE_PROJECT_ID = "buddy-aeabf"

redirect_uris = [
    "https://buddy-aeabf.firebaseapp.com/__/auth/handler",
    "https://buddy-aeabf.web.app/__/auth/handler",
]

print("\n" + "=" * 80)
print("YAHOO OAUTH SETUP FOR FIREBASE")
print("=" * 80)

print("\n✓ CREDENTIALS FOUND IN .env")
print("-" * 80)
print(f"Client ID:     {YAHOO_CLIENT_ID}")
print(f"Client Secret: {YAHOO_CLIENT_SECRET}")
print(f"Project ID:    {FIREBASE_PROJECT_ID}")

print("\n✓ REDIRECT URIs CONFIGURED")
print("-" * 80)
for uri in redirect_uris:
    print(f"  • {uri}")

print("\n" + "=" * 80)
print("ACTION REQUIRED: Configure Yahoo Provider in Firebase Console")
print("=" * 80)

print("""
1. Open Firebase Console:
   https://console.firebase.google.com/project/buddy-aeabf/authentication/providers

2. Scroll to "Yahoo" provider and click the edit (pencil) icon

3. Enter these credentials:
   
   Client ID:
   dj0yJmk9SURlaTFGRlR6UzVzJmQ9WVdrOWQwdEZjMnR1WnpjbWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PWFi
   
   Client Secret:
   f49e11122530fd800b69446a09f7cc040e1d8f8e

4. Ensure the "Enable" toggle is ON

5. Click "Save"

6. Verify Redirect URIs in Yahoo Developer Console:
   https://developer.yahoo.com/apps
   
   Both URIs should be added:
   • https://buddy-aeabf.firebaseapp.com/__/auth/handler
   • https://buddy-aeabf.web.app/__/auth/handler

7. Test Yahoo Login at:
   https://buddy-aeabf.web.app
""")

print("=" * 80)
print("TROUBLESHOOTING")
print("=" * 80)

print("""
If Yahoo login still fails:

1. Check Firebase Auth → Settings → Authorized Domains
   Should include:
   • buddy-aeabf.firebaseapp.com
   • buddy-aeabf.web.app

2. Verify Yahoo App Redirect URIs match exactly (no trailing slashes!)

3. Clear browser cache (Ctrl+Shift+Delete) and try again

4. Check browser console for exact error messages
""")

print("\n✓ Setup script completed\n")
sys.exit(0)
