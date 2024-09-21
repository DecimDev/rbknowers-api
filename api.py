from fastapi import FastAPI, HTTPException
import nfl_data_py as nfl
import pandas as pd
import numpy as np
from datetime import datetime
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_most_recent_game(team_abbr):
    logger.info(f"Fetching schedule for team: {team_abbr}")
    schedule = nfl.import_schedules([2024])
    if schedule.empty:
        raise ValueError("Schedule data is empty")

    team_games = schedule[(schedule['home_team'] == team_abbr) | (schedule['away_team'] == team_abbr)]
    if team_games.empty:
        raise ValueError(f"No games found for team {team_abbr}")

    team_games['gameday'] = pd.to_datetime(team_games['gameday'])
    today = pd.to_datetime(datetime.today().date())
    recent_games = team_games[team_games['gameday'] <= today]

    if recent_games.empty:
        raise ValueError(f"No recent games found for team {team_abbr}")

    most_recent_game = recent_games.sort_values(by='gameday', ascending=False).iloc[0]
    logger.info(f"Most recent game ID: {most_recent_game['game_id']}")
    return most_recent_game['game_id']

def get_season_games(team_abbr):
    logger.info(f"Fetching season games for team: {team_abbr}")
    schedule = nfl.import_schedules([2024])
    if schedule.empty:
        raise ValueError("Schedule data is empty")

    team_games = schedule[(schedule['home_team'] == team_abbr) | (schedule['away_team'] == team_abbr)]
    if team_games.empty:
        raise ValueError(f"No games found for team {team_abbr}")

    team_games['gameday'] = pd.to_datetime(team_games['gameday'])
    today = pd.to_datetime(datetime.today().date())
    season_games = team_games[team_games['gameday'] <= today]

    if season_games.empty:
        raise ValueError(f"No season games found for team {team_abbr}")

    return season_games['game_id'].tolist()

@app.get("/epa-per-play/{team_abbr}")
async def get_epa_per_play(team_abbr: str):
    try:
        game_id = get_most_recent_game(team_abbr)
        season_game_ids = get_season_games(team_abbr)
    except ValueError as e:
        logger.error(f"Error fetching game data: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    pbp_cols = nfl.see_pbp_cols()
    pbp_data = nfl.import_pbp_data([2024], include_participation=False)
    pfr_data = nfl.import_weekly_pfr('pass', [2024])
    # Get column headers for pfr_data
    pfr_headers = pfr_data.columns.tolist()
    logger.info(f"PFR data columns: {pfr_headers}")
    print(pfr_headers)
    if pbp_data.empty:
        logger.error("Play-by-play data is empty")
        raise HTTPException(status_code=404, detail="Play-by-play data is empty")

    # Most recent game data
    game_plays = pbp_data[pbp_data['game_id'] == game_id]
    if game_plays.empty:
        logger.error(f"No plays found for game {game_id}")
        raise HTTPException(status_code=404, detail=f"No plays found for game {game_id}")

    game_plays = game_plays[game_plays['epa'].notnull()]
    epa_per_play_recent = game_plays[['play_id', 'posteam', 'defteam', 'desc', 'epa']].to_dict(orient='records')

    # Season data
    season_plays = pbp_data[pbp_data['game_id'].isin(season_game_ids)]
    season_plays = season_plays[season_plays['epa'].notnull()]
    epa_per_play_season = season_plays[['play_id', 'posteam', 'defteam', 'desc', 'epa']].to_dict(orient='records')

    # Replace NaN values with None and convert numpy types to native Python types
    epa_per_play_recent = [{k: (v if pd.notna(v) else None) for k, v in play.items()} for play in epa_per_play_recent]
    epa_per_play_recent = [{k: (v.item() if isinstance(v, (np.generic, np.ndarray)) else v) for k, v in play.items()} for play in epa_per_play_recent]

    epa_per_play_season = [{k: (v if pd.notna(v) else None) for k, v in play.items()} for play in epa_per_play_season]
    epa_per_play_season = [{k: (v.item() if isinstance(v, (np.generic, np.ndarray)) else v) for k, v in play.items()} for play in epa_per_play_season]

    pbp_cols_list = list(pbp_cols)
    return {
        "most_recent_game": {"game_id": game_id, "epa_per_play": epa_per_play_recent},
        "season": {"game_ids": season_game_ids, "epa_per_play": epa_per_play_season},
        "pbp_cols": pbp_cols_list
    }

@app.get("/qb-performance/{team_abbr}")
async def get_qb_performance(team_abbr: str):
    try:
        game_id = get_most_recent_game(team_abbr)
        season_game_ids = get_season_games(team_abbr)
    except ValueError as e:
        logger.error(f"Error fetching game data: {e}")
        raise HTTPException(status_code=404, detail=str(e))

    pbp_data = nfl.import_pbp_data([2024], include_participation=False)

    if pbp_data.empty:
        logger.error("Play-by-play data is empty")
        raise HTTPException(status_code=404, detail="Play-by-play data is empty")

    # Most recent game data
    game_plays = pbp_data[pbp_data['game_id'] == game_id]
    if game_plays.empty:
        logger.error(f"No plays found for game {game_id}")
        raise HTTPException(status_code=404, detail=f"No plays found for game {game_id}")

    qb_plays_recent = game_plays[
        (game_plays['posteam'] == team_abbr) & 
        (game_plays['play_type'].isin(['pass', 'run'])) &
        (game_plays['qb_dropback'] == 1)
    ]

    if qb_plays_recent.empty:
        logger.error(f"No QB plays found for team {team_abbr}")
        raise HTTPException(status_code=404, detail=f"No QB plays found for team {team_abbr}")

    qb_name_recent = qb_plays_recent['passer_player_name'].mode().iloc[0]
    completions_recent = qb_plays_recent['complete_pass'].sum()
    attempts_recent = qb_plays_recent['pass_attempt'].sum()
    passing_yards_recent = qb_plays_recent['passing_yards'].sum()
    passing_tds_recent = qb_plays_recent['pass_touchdown'].sum()
    interceptions_recent = qb_plays_recent['interception'].sum()
    sacks_recent = qb_plays_recent['sack'].sum()
    sack_yards_recent = qb_plays_recent['sack_yards'].sum()

    any_a_recent = (passing_yards_recent + 20 * passing_tds_recent - 45 * interceptions_recent - sack_yards_recent) / (attempts_recent + sacks_recent)
    
    qb_performance_recent = {
        "qb_name": qb_name_recent,
        "game_id": game_id,
        "epa": float(qb_plays_recent['epa'].sum()),
        "epa_per_play": float(qb_plays_recent['epa'].mean()),
        "cpoe": float(qb_plays_recent['cpoe'].mean()),
        "completion_percentage": (completions_recent / attempts_recent * 100) if attempts_recent > 0 else 0,
        "touchdowns": int(passing_tds_recent),
        "interceptions": int(interceptions_recent),
        "attempts": int(attempts_recent),
        "completions": int(completions_recent),
        "any_a": float(any_a_recent)
    }

    # Season data
    season_plays = pbp_data[pbp_data['game_id'].isin(season_game_ids)]
    qb_plays_season = season_plays[
        (season_plays['posteam'] == team_abbr) & 
        (season_plays['play_type'].isin(['pass', 'run'])) &
        (season_plays['qb_dropback'] == 1)
    ]

    if qb_plays_season.empty:
        logger.error(f"No QB plays found for team {team_abbr} in the season")
        raise HTTPException(status_code=404, detail=f"No QB plays found for team {team_abbr} in the season")

    qb_name_season = qb_plays_season['passer_player_name'].mode().iloc[0]
    completions_season = qb_plays_season['complete_pass'].sum()
    attempts_season = qb_plays_season['pass_attempt'].sum()
    passing_yards_season = qb_plays_season['passing_yards'].sum()
    passing_tds_season = qb_plays_season['pass_touchdown'].sum()
    interceptions_season = qb_plays_season['interception'].sum()
    sacks_season = qb_plays_season['sack'].sum()
    sack_yards_season = qb_plays_season['sack_yards'].sum()

    any_a_season = (passing_yards_season + 20 * passing_tds_season - 45 * interceptions_season - sack_yards_season) / (attempts_season + sacks_season)
    
    qb_performance_season = {
        "qb_name": qb_name_season,
        "game_ids": season_game_ids,
        "epa": float(qb_plays_season['epa'].sum()),
        "epa_per_play": float(qb_plays_season['epa'].mean()),
        "cpoe": float(qb_plays_season['cpoe'].mean()),
        "completion_percentage": (completions_season / attempts_season * 100) if attempts_season > 0 else 0,
        "touchdowns": int(passing_tds_season),
        "interceptions": int(interceptions_season),
        "attempts": int(attempts_season),
        "completions": int(completions_season),
        "any_a": float(any_a_season)
    }

    return {
        "most_recent_game": qb_performance_recent,
        "season": qb_performance_season
    }
