from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .config import settings
from .database import Base, engine
from . import models
from .middleware import write_rate_limit
from .routers import workspace, audits, analytics, evidence, reports, actions, imports

@asynccontextmanager
async def lifespan(app:FastAPI):
    # For quickstart. In production, run migrations instead of relying on create_all.
    Base.metadata.create_all(bind=engine)
    yield

app=FastAPI(title='EcoSphere AI API',version='0.1.0',lifespan=lifespan)
app.middleware('http')(write_rate_limit)
app.add_middleware(CORSMiddleware,allow_origins=[o.strip() for o in settings.allowed_origins.split(',') if o.strip()],allow_credentials=True,allow_methods=['GET','POST','PUT','DELETE'],allow_headers=['Authorization','Content-Type'])
for router in (workspace.router,audits.router,analytics.router,evidence.router,reports.router,actions.router,imports.router): app.include_router(router)

@app.get('/api/health')
def health():return {'status':'ok','mode':'local-development' if settings.dev_auth_mode else 'supabase-auth'}
