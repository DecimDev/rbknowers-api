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

def get_qb_performance_for_game(pbp_data, season_game_ids, team_abbr):
    # Check if play-by-play data is empty
    if not season_game_ids:
        logger.error(f"No season games found for team {team_abbr}")
        return {}  # Return an empty object instead of raising an exception

    most_recent_game_id = season_game_ids[-1]
    print(most_recent_game_id)
    logger.info(f"Most recent game ID from season games: {most_recent_game_id}")
    if pbp_data.empty:
        logger.error(f"No plays found for game {most_recent_game_id}")
        return {}  # Return an empty object instead of raising an exception

    game_plays = pbp_data[pbp_data['game_id'] == most_recent_game_id]
    if game_plays.empty:
        logger.error(f"No plays found for game {most_recent_game_id}")
        most_recent_game_id = season_game_ids[-2]
        game_plays = pbp_data[pbp_data['game_id'] == most_recent_game_id]

    qb_plays = filter_qb_plays(game_plays, team_abbr)
    if qb_plays.empty:
        logger.error(f"No QB plays found for team {team_abbr}")
        return {}  # Return an empty object instead of raising an exception

    return calculate_qb_performance(qb_plays, game_plays, team_abbr, most_recent_game_id)

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
        "epa": round(float(qb_plays['epa'].sum()), 3),
        "epa_per_play": round(float(qb_plays['epa'].mean()), 3),
        "cpoe": round(float(qb_plays['cpoe'].mean()), 3),
        "completion_percentage": round((completions / attempts * 100) if attempts > 0 else 0, 1),
        "touchdowns": round(float(passing_tds), 0),
        "interceptions": round(float(interceptions), 0),
        "attempts": round(float(attempts), 0),
        "completions": int(completions),
        "any_a": round(float(any_a), 3)
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

    total_yards_lost = round(-qualified_qb_plays[qualified_qb_plays['sack'] == 1]['yards_gained'].sum(), 0)
    total_attempts = round(qualified_qb_plays['pass_attempt'].sum(), 0)
    total_sacks = round(qualified_qb_plays['sack'].sum(), 0)
    total_passing_yards = round(qualified_qb_plays['passing_yards'].sum(), 0)
    total_passing_tds = round(qualified_qb_plays['pass_touchdown'].sum(), 0)
    total_interceptions = round(qualified_qb_plays['interception'].sum(), 0)
    
    print(total_attempts)
    print(total_sacks)
    print(total_passing_yards)
    print(total_passing_tds)
    print(total_interceptions)
    print(total_yards_lost)
    
    qualified_any_a = (total_passing_yards + 20 * total_passing_tds - 45 * total_interceptions - total_yards_lost) / (total_attempts + total_sacks)

    return {
        "epa": round(float(avg_stats['epa']), 3),
        "epa_per_play": round(float(avg_stats['epa']), 3),
        "cpoe": round(float(avg_stats['cpoe']), 3),
        "completion_percentage": round((avg_stats['complete_pass'] / avg_stats['pass_attempt']) * 100, 1),
        "touchdowns": round(float(avg_stats['pass_touchdown']), 0),
        "interceptions": round(float(avg_stats['interception']), 0),
        "attempts": round(float(avg_stats['pass_attempt']), 0),
        "completions": round(float(avg_stats['complete_pass']), 0),
        "any_a": round(float(qualified_any_a), 3)
    }