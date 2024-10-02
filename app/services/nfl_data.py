from http.client import HTTPException
import nfl_data_py as nfl
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from fastapi import HTTPException

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

