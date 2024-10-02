from fastapi import APIRouter, HTTPException
from app.services.qb_data import get_qb_stats
router = APIRouter()

@router.get("/{team_abbr}")
async def get_qb_weekly_performance(team_abbr: str):
    try:       
        qb_stats_per_week = get_qb_stats(team_abbr)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return qb_stats_per_week
