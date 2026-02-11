# Deploy Backend from Local Docker Build
Write-Host "Local Build to Cloud Deploy" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path "Back_End")) {
    Write-Host "ERROR: Run from project root" -ForegroundColor Red
    exit 1
}

Write-Host "Step 1/4: Building locally..." -ForegroundColor Cyan
docker build -t gcr.io/buddy-aeabf/buddy-app:latest .
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "Build OK" -ForegroundColor Green

Write-Host "Step 2/4: Configuring Docker..." -ForegroundColor Cyan
gcloud auth configure-docker gcr.io --quiet
Write-Host "Docker configured" -ForegroundColor Green

Write-Host "Step 3/4: Pushing to GCR..." -ForegroundColor Cyan
docker push gcr.io/buddy-aeabf/buddy-app:latest
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "Pushed" -ForegroundColor Green

Write-Host "Step 4/4: Deploying..." -ForegroundColor Cyan
gcloud run deploy buddy-app --image gcr.io/buddy-aeabf/buddy-app:latest --region us-east4 --project buddy-aeabf --allow-unauthenticated --no-traffic
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "DONE!" -ForegroundColor Green
$rev = gcloud run services describe buddy-app --region us-east4 --project buddy-aeabf --format='value(status.latestReadyRevisionName)'
Write-Host "New revision: $rev"
