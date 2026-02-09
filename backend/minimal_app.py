from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()


@app.get("/")
async def root():
    return HTMLResponse(
        "<html><body><h1>Buddy Backend: Test OK</h1><p>Deployment is live.</p></body></html>"
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
