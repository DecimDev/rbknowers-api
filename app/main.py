from fastapi import FastAPI
from app.api.endpoints import general_team_info, qb_performance
from app.core.logger import setup_logging

# Set up logging
setup_logging()

# Create FastAPI app
app = FastAPI()

# Include routers
app.include_router(qb_performance.router, prefix="/qb-performance", tags=["QB Performance"])
app.include_router(general_team_info.router, prefix="/general-team-info", tags=["General Team Info"])
# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}