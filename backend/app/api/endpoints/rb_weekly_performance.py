import logging
from fastapi import APIRouter, HTTPException
from app.services.rb_data import get_rb_stats

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/{team_abbr}")
async def get_rb_weekly_performance(team_abbr: str):
    try:
        rb_stats = get_rb_stats(team_abbr)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return rb_stats
