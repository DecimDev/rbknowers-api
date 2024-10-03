from fastapi import FastAPI
from app.api.endpoints import general_team_info, qb_weekly_performance, wr_weekly_performance, rb_weekly_performance
from app.core.logger import setup_logging

# Set up logging
setup_logging()

# Create FastAPI app
app = FastAPI()

# Include routers
app.include_router(general_team_info.router, prefix="/general-team-info", tags=["General Team Info"])
app.include_router(qb_weekly_performance.router, prefix="/qb-weekly-performance", tags=["QB Weekly Performance"])
app.include_router(wr_weekly_performance.router, prefix="/wr-weekly-performance", tags=["WR Weekly Performance"])
app.include_router(rb_weekly_performance.router, prefix="/rb-weekly-performance", tags=["RB Weekly Performance"])
# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}