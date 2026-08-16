
from pathlib import Path
import pandas as pd
from .parser import parse_result_html

def load_html_to_db(con, path_or_file):
    race, runners = parse_result_html(path_or_file)
    if not race.get("race_id"):
        return {"ok":False, "message":"race_idを取得できませんでした"}

    race_df = pd.DataFrame([race])
    con.register("race_in", race_df)
    con.execute("""
      INSERT OR REPLACE INTO races
      SELECT race_id, CAST(race_date AS DATE), venue, race_no, race_name,
             surface, distance_m, going, source_file
      FROM race_in
    """)

    if not runners.empty:
        con.register("runner_in", runners)
        con.execute("""
          INSERT OR REPLACE INTO runners
          SELECT race_id, horse_no, horse_name, sex_age, jockey_name,
                 weight_carried, odds, popularity, finish_position,
                 finish_time, last3f, corner_order, source_file
          FROM runner_in
        """)
    return {"ok":True, "race_id":race["race_id"], "runners":len(runners)}
