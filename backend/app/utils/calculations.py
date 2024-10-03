import pandas as pd

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