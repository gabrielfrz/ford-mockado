"""Local demonstration API. Original routes/models remain in their original folders."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.demo_routes import router

app = FastAPI(title='DANDR Dashboard API — Synthetic Demo', version='1.0.0',
              description='Local synthetic records. No authentication, BigQuery or real database connection.')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:4200','http://127.0.0.1:4200'],
                   allow_methods=['GET'], allow_headers=['*'])

@app.get('/health')
def health():
    return {'status': 'ok', 'data_source': 'synthetic', 'cloud_connections': False}

app.include_router(router)
