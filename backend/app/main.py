from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.municipios import router as municipios_router
from app.utils.config import settings

app = FastAPI(
    title="FUNDEB Insights API",
    description=(
        "Plataforma de inteligência para dados públicos da educação brasileira. "
        "Consolida FUNDEB, IDEB e IBGE em uma API analítica para consumo do frontend."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(municipios_router)


@app.get("/health", tags=["infra"])
def health_check() -> dict:
    return {"status": "ok", "version": "0.1.0"}
