import logging
import numpy as np
import nfl_data_py as nfl
from app.services.nfl_data import get_season_games
import json

logger = logging.getLogger(__name__)

def safe_float(value):
    if isinstance(value, (np.number, float)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    return value

def get_qb_stats(team_abbr):
    weekly_stats = nfl.import_weekly_data([2024])
    pbp_data = nfl.import_pbp_data([2024], include_participation=False)
    season_game_ids = get_season_games(team_abbr)
    season_plays = pbp_data[pbp_data['game_id'].isin(season_game_ids)]
    qb_plays = filter_qb_plays(season_plays, team_abbr)
    
    player_ids = qb_plays['passer_player_id'].dropna().unique()
        
    qb_stats = weekly_stats[weekly_stats['player_id'].isin(player_ids)]
    
    qb_stats_per_week = qb_stats.groupby(['player_id', 'week'], as_index=False).agg({
        'player_name': 'first',
        'passing_epa': 'sum',
        'completions': 'sum',
        'attempts': 'sum',
        'passing_yards': 'sum',
        'passing_tds': 'sum',
        'interceptions': 'sum',
        'sacks': 'sum',
        'sack_yards': 'sum',
        'passing_epa': 'sum',
        'rushing_epa': 'sum',
        'dakota': 'mean'
    })
    
    # Calculate ANY/A for each record
    qb_stats_per_week['any_a'] = qb_stats_per_week.apply(lambda row: 
        ((row['passing_yards'] + 20 * row['passing_tds'] - 45 * row['interceptions'] - row['sack_yards'])) / (row['attempts'] + row['sacks']) 
        if (row['attempts'] + row['sacks']) > 0 else 0.0, axis=1)
    
    # Convert to regular Python types and handle NaN values
    qb_stats_json = json.loads(qb_stats_per_week.to_json(orient='records', date_format='iso'))
    
    # Replace NaN with None for JSON compatibility
    for stat in qb_stats_json:
        for key, value in stat.items():
            if value != value:  # Check for NaN
                stat[key] = None
    
    return qb_stats_json

def filter_qb_plays(plays, team_abbr):
    return plays[
        (plays['posteam'] == team_abbr) & 
        (plays['play_type'].isin(['pass', 'run'])) &
        (plays['qb_dropback'] == 1)
    ]