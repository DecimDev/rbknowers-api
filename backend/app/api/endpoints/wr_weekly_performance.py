from fastapi import APIRouter, HTTPException
from app.services.wr_data import get_wr_stats

router = APIRouter()

@router.get("/{team_abbr}")
async def get_wr_weekly_performance(team_abbr: str):
    try:
        wr_stats = get_wr_stats(team_abbr)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return wr_stats
