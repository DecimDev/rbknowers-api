from fastapi import APIRouter, HTTPException
import nfl_data_py as nfl

router = APIRouter()

@router.get("/{team_abbr}")
async def get_general_team_info(team_abbr: str):
    try:
        teams_desc = nfl.import_team_desc()
        team_desc = teams_desc[teams_desc['team_abbr'] == team_abbr]
        team_desc = team_desc.to_dict(orient='records')
        return {"team_desc": team_desc}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
