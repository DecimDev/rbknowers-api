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

def get_qb_performance_for_game(pbp_data, game_id, team_abbr):
    game_plays = pbp_data[pbp_data['game_id'] == game_id]
    if game_plays.empty:
        logger.error(f"No plays found for game {game_id}")
        raise HTTPException(status_code=204, detail=f"No plays found for game {game_id}")

    qb_plays = filter_qb_plays(game_plays, team_abbr)
    if qb_plays.empty:
        logger.error(f"No QB plays found for team {team_abbr}")
        raise HTTPException(status_code=204, detail=f"No QB plays found for team {team_abbr}")

    return calculate_qb_performance(qb_plays, game_plays, team_abbr, game_id)

def get_qb_performance_for_season(pbp_data, season_game_ids, team_abbr):
    season_plays = pbp_data[pbp_data['game_id'].isin(season_game_ids)]
    qb_plays = filter_qb_plays(season_plays, team_abbr)
    if qb_plays.empty:
        logger.error(f"No QB plays found for team {team_abbr} in the season")
        raise HTTPException(status_code=204, detail=f"No QB plays found for team {team_abbr} in the season")

    return calculate_qb_performance(qb_plays, season_plays, team_abbr, season_game_ids)

def filter_qb_plays(plays, team_abbr):
    return plays[
        (plays['posteam'] == team_abbr) & 
        (plays['play_type'].isin(['pass', 'run'])) &
        (plays['qb_dropback'] == 1)
    ]

def calculate_qb_performance(qb_plays, all_plays, team_abbr, game_id):
    qb_name = qb_plays['passer_player_name'].mode().iloc[0]
    completions = qb_plays['complete_pass'].sum()
    attempts = qb_plays['pass_attempt'].sum()
    passing_yards = qb_plays['passing_yards'].sum()
    passing_tds = qb_plays['pass_touchdown'].sum()
    interceptions = qb_plays['interception'].sum()
    sacks = qb_plays['sack'].sum()

    sack_plays = all_plays[(all_plays['sack'] == 1) & (all_plays['posteam'] == team_abbr)]
    total_yards_lost = -sack_plays['yards_gained'].sum()

    any_a = (passing_yards + 20 * passing_tds - 45 * interceptions - total_yards_lost) / (attempts + sacks)

    return {
        "qb_name": qb_name,
        "game_id": game_id,
        "epa": float(qb_plays['epa'].sum()),
        "epa_per_play": float(qb_plays['epa'].mean()),
        "cpoe": float(qb_plays['cpoe'].mean()),
        "completion_percentage": (completions / attempts * 100) if attempts > 0 else 0,
        "touchdowns": int(passing_tds),
        "interceptions": int(interceptions),
        "attempts": int(attempts),
        "completions": int(completions),
        "any_a": float(any_a)
    }

def get_average_qb_performance(pbp_data):
    season_plays = pbp_data[pbp_data['game_id'].notnull()]
    qb_plays_all = season_plays[
        (season_plays['play_type'].isin(['pass', 'run'])) &
        (season_plays['qb_dropback'] == 1)
    ]

    qb_snap_counts = qb_plays_all.groupby('passer_player_name').size()
    qualified_qbs = qb_snap_counts[qb_snap_counts > 30].index
    qualified_qb_plays = qb_plays_all[qb_plays_all['passer_player_name'].isin(qualified_qbs)]

    avg_stats = qualified_qb_plays.groupby('passer_player_name').agg({
        'epa': 'mean',
        'cpoe': 'mean',
        'complete_pass': 'sum',
        'pass_attempt': 'sum',
        'passing_yards': 'sum',
        'pass_touchdown': 'sum',
        'interception': 'sum',
        'sack': 'sum'
    }).mean()

    total_yards_lost = -qualified_qb_plays[qualified_qb_plays['sack'] == 1]['yards_gained'].sum()
    total_attempts = qualified_qb_plays['pass_attempt'].sum()
    total_sacks = qualified_qb_plays['sack'].sum()
    total_passing_yards = qualified_qb_plays['passing_yards'].sum()
    total_passing_tds = qualified_qb_plays['pass_touchdown'].sum()
    total_interceptions = qualified_qb_plays['interception'].sum()

    qualified_any_a = (total_passing_yards + 20 * total_passing_tds - 45 * total_interceptions - total_yards_lost) / (total_attempts + total_sacks)

    return {
        "epa": float(avg_stats['epa']),
        "epa_per_play": float(avg_stats['epa']),
        "cpoe": float(avg_stats['cpoe']),
        "completion_percentage": float((avg_stats['complete_pass'] / avg_stats['pass_attempt']) * 100),
        "touchdowns": float(avg_stats['pass_touchdown']),
        "interceptions": float(avg_stats['interception']),
        "attempts": float(avg_stats['pass_attempt']),
        "completions": float(avg_stats['complete_pass']),
        "any_a": float(qualified_any_a)
    }

@app.get("/pbp-columns")
async def get_pbp_columns():
    try:
        # Import a small sample of play-by-play data
        pbp_data = nfl.import_pbp_data([2024], include_participation=False)
        
        if pbp_data.empty:
            logger.error("Play-by-play data is empty")
            raise HTTPException(status_code=204, detail="Play-by-play data is empty")
        
        # Get the column names
        columns = pbp_data.columns.tolist()
        play_types = pbp_data['play_type'].unique().tolist()

        return {"columns": columns, "play_types": play_types}
    
    except Exception as e:
        logger.error(f"Error fetching play-by-play columns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/qb-performance/{team_abbr}")
async def get_qb_performance(team_abbr: str):
    try:
        game_id = get_most_recent_game(team_abbr)
        season_game_ids = get_season_games(team_abbr)
    except ValueError as e:
        logger.error(f"Error fetching game data: {e}")
        raise HTTPException(status_code=204, detail=str(e))

    pbp_data = nfl.import_pbp_data([2024], include_participation=False)

    if pbp_data.empty:
        logger.error("Play-by-play data is empty")
        raise HTTPException(status_code=204, detail="Play-by-play data is empty")

    qb_performance_recent = get_qb_performance_for_game(pbp_data, game_id, team_abbr)
    qb_performance_season = get_qb_performance_for_season(pbp_data, season_game_ids, team_abbr)
    avg_qb_performance = get_average_qb_performance(pbp_data)

    return {
        "most_recent_game": qb_performance_recent,
        "season": qb_performance_season,
        "league_average": avg_qb_performance
    }