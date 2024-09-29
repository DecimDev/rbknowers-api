from fastapi import APIRouter, HTTPException
import nfl_data_py as nfl
from app.services.nfl_data import get_most_recent_game, get_season_games, get_average_qb_performance, get_qb_performance_for_game, get_qb_performance_for_season

router = APIRouter()

@router.get("/{team_abbr}")
async def get_qb_performance(team_abbr: str):
    try:
        game_id = get_most_recent_game(team_abbr)
        season_game_ids = get_season_games(team_abbr)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    pbp_data = nfl.import_pbp_data([2024], include_participation=False)
    if pbp_data.empty:
        raise HTTPException(status_code=404, detail="Play-by-play data is empty")
    
    print(season_game_ids)

    qb_performance_recent = get_qb_performance_for_game(pbp_data, season_game_ids, team_abbr)
    qb_performance_season = get_qb_performance_for_season(pbp_data, season_game_ids, team_abbr)
    avg_qb_performance = get_average_qb_performance(pbp_data)

    return {
        "most_recent_game": qb_performance_recent,
        "season": qb_performance_season,
        "league_average": avg_qb_performance
    }