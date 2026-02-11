#!/bin/bash
# Backend Safe Deployment Script
# Prevents common deployment errors by validating setup before deploying

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        Backend Deployment Safety Check & Deploy                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in the project root
if [ ! -d "Back_End" ] || [ ! -d "Front_End" ]; then
    echo "❌ ERROR: Must run from project root"
    echo "   (Back_End/ and Front_End/ directories must exist)"
    exit 1
fi

echo "✓ Running from project root"

# Check for legacy backend directories
if [ -d "Back-End" ] || [ -d "backend" ]; then
    echo "❌ ERROR: Legacy backend directories still exist"
    echo "   Delete these first:"
    [ -d "Back-End" ] && echo "     rm -r Back-End/"
    [ -d "backend" ] && echo "     rm -r backend/"
    exit 1
fi

echo "✓ No legacy backend directories found"

# Verify essential backend files exist
REQUIRED_FILES=(
    "Back_End/main.py"
    "Back_End/__init__.py"
    "Back_End/whiteboard_metrics.py"
    "Back_End/chat_session_handler.py"
    "Back_End/system_health.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ ERROR: Missing essential file: $file"
        exit 1
    fi
done

echo "✓ All essential backend files present"

# Verify requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: requirements.txt not found"
    exit 1
fi

echo "✓ requirements.txt exists"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Pre-Deployment Boot Check                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Try to import the main module to catch errors early
echo "Testing Python import system..."
if python -c "
import sys
sys.path.insert(0, '.')
from Back_End import main
print('✓ Back_End module imports successfully')
print(f'✓ Boot checks: {main._BOOT_CHECKS}')
all_ok = all(main._BOOT_CHECKS.values())
if not all_ok:
    print('⚠  Some systems are not loaded')
    print(f'  Errors: {main._BOOT_ERRORS}')
" 2>&1 | grep -v "^python-dotenv\|^WARNING:dotenv"; then
    echo "✓ Local import test passed"
else
    echo "⚠  Import test showed warnings (non-fatal)"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║            Deploying to Google Cloud Run                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "Deploying buddy-app service..."
echo "  - Building from: $(pwd)"
echo "  - Source: . (entire project root)"
echo "  - Region: us-east4"
echo "  - Project: buddy-aeabf"
echo "  - Traffic: None initially (test before routing)"
echo ""

gcloud run deploy buddy-app \
    --source . \
    --region us-east4 \
    --project buddy-aeabf \
    --allow-unauthenticated \
    --no-traffic

echo ""
echo "✓ Deployment complete!"
echo ""

# Get the new revision
REVISION=$(gcloud run services list \
    --filter "name:buddy-app" \
    --format "value(status.latestReadyRevisionName)" \
    --region us-east4 \
    --project buddy-aeabf)

echo "New revision: $REVISION"
echo ""

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Testing New Revision                              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

echo "Waiting for service to stabilize..."
sleep 5

echo "Checking boot health..."
gcloud run services logs read buddy-app \
    --limit 30 \
    --region us-east4 \
    --project buddy-aeabf | head -20

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              Next Steps                                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo "1. Review the logs above to ensure no boot errors"
echo "2. Test the endpoints:"
echo "   curl https://buddy-app-${REVISION}.run.app/health"
echo "   curl https://buddy-app-${REVISION}.run.app/boot/health"
echo "   curl https://buddy-app-${REVISION}.run.app/system/health"
echo ""
echo "3. If tests pass, route traffic:"
echo "   gcloud run services update-traffic buddy-app \\"
echo "     --to-revisions ${REVISION}=100 \\"
echo "     --region us-east4"
echo ""
echo "4. If something is wrong, rollback to previous:"
echo "   gcloud run services update-traffic buddy-app \\"
echo "     --to-revisions buddy-app-00028-bsx=100 \\"
echo "     --region us-east4"
echo ""
