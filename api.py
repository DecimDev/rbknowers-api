from fastapi import FastAPI, HTTPException
import nfl_data_py as nfl
import pandas as pd
from datetime import datetime

app = FastAPI()

def get_most_recent_game(team_abbr):
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
    return most_recent_game['game_id']

@app.get("/epa-per-play/{team_abbr}")
async def get_epa_per_play(team_abbr: str):
    try:
        game_id = get_most_recent_game(team_abbr)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    pbp_data = nfl.import_pbp_data([2024], include_participation=False)
    if pbp_data.empty:
        raise HTTPException(status_code=404, detail="Play-by-play data is empty")

    game_plays = pbp_data[pbp_data['game_id'] == game_id]
    if game_plays.empty:
        raise HTTPException(status_code=404, detail=f"No plays found for game {game_id}")

    # Filter out plays where EPA is not available
    game_plays = game_plays[game_plays['epa'].notnull()]

    # Convert the result to a dictionary
    epa_per_play = game_plays[['play_id', 'posteam', 'defteam', 'desc', 'epa']].to_dict(orient='records')

    return {"game_id": game_id, "epa_per_play": epa_per_play}
