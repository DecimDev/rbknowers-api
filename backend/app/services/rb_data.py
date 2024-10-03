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

def get_rb_stats(team_abbr):
    weekly_stats = nfl.import_weekly_data([2024])
    pbp_data = nfl.import_pbp_data([2024], include_participation=False)
    season_game_ids = get_season_games(team_abbr)
    season_plays = pbp_data[pbp_data['game_id'].isin(season_game_ids)]
    rb_plays = filter_rb_plays(season_plays, team_abbr)
    
    player_ids = rb_plays['rusher_player_id'].dropna().unique()
    
    rb_stats = weekly_stats[weekly_stats['player_id'].isin(player_ids)]
    
    rb_stats_per_week = rb_stats.groupby(['player_id', 'week'], as_index=False).agg({
        'player_name': 'first',
        'rushing_epa': 'sum',
        'rushing_yards': 'sum',
        'carries': 'sum',
        'rushing_tds': 'sum',
        'rushing_fumbles': 'sum',
        'rushing_first_downs': 'sum',
    })
    
    # Convert to regular Python types and handle NaN values
    rb_stats_json = json.loads(rb_stats_per_week.to_json(orient='records', date_format='iso'))
    
    # Replace NaN with None for JSON compatibility
    for stat in rb_stats_json:
        for key, value in stat.items():
            if value != value:  # Check for NaN
                stat[key] = None
    
    return rb_stats_json

def filter_rb_plays(plays, team_abbr):
    return plays[
        (plays['posteam'] == team_abbr) &
        (plays['play_type'].isin(['run'])) &
        (plays['rusher_player_id'].notna())
    ]
