from fastapi import FastAPI
from app.api import incentives_router, companies_router, data_management_router, chatbot_router, web_interface_router

app = FastAPI(
    title="Public Incentives API",
    description="API para identificar empresas adequadas a incentivos públicos em Portugal",
    version="1.0.0"
)

# Include routers
app.include_router(incentives_router)
app.include_router(companies_router)
app.include_router(data_management_router)
app.include_router(chatbot_router)
app.include_router(web_interface_router)

@app.get("/health")
def health():
    return {"status": "ok", "message": "Public Incentives API is running"}

@app.get("/")
def root():
    return {
        "message": "Public Incentives API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
