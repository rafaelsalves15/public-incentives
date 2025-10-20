from fastapi import FastAPI

app = FastAPI(title="Public Incentives API")

@app.get("/health")
def health():
    return {"status": "ok"}
