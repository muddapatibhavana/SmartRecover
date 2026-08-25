import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.entities import Customer
from app.seed import seed_database
from app.api import (
    dashboard,
    recovery_cases,
    audit,
    human_review,
    simulator,
    demo,
    optimizer,
    what_if,
    prioritization,
    stress_test
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("smartrecover")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure tables are created and initial demo seed exists
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        cust_count = db.query(Customer).count()
        if cust_count == 0:
            logger.info("Database is empty. Automatically seeding demo dataset...")
            seed_database(db=db)
    finally:
        db.close()
    yield
    # Shutdown
    logger.info("SmartRecover service shutting down.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.TAGLINE,
    version="1.0.0",
    docs_url=f"{settings.API_PREFIX}/docs",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(dashboard.router, prefix=settings.API_PREFIX)
app.include_router(recovery_cases.router, prefix=settings.API_PREFIX)
app.include_router(audit.router, prefix=settings.API_PREFIX)
app.include_router(human_review.router, prefix=settings.API_PREFIX)
app.include_router(simulator.router, prefix=settings.API_PREFIX)
app.include_router(demo.router, prefix=settings.API_PREFIX)
app.include_router(optimizer.router, prefix=settings.API_PREFIX)
app.include_router(what_if.router, prefix=settings.API_PREFIX)
app.include_router(prioritization.router, prefix=settings.API_PREFIX)
app.include_router(stress_test.router, prefix=settings.API_PREFIX)

@app.get(f"{settings.API_PREFIX}/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "env": settings.APP_ENV,
        "principle": "AI recommends. Guardrails control. Automation stops safely."
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to SmartRecover API",
        "docs": f"{settings.API_PREFIX}/docs",
        "health": f"{settings.API_PREFIX}/health"
    }
