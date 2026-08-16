
import duckdb

SCHEMA = """
CREATE TABLE IF NOT EXISTS races(
  race_id VARCHAR PRIMARY KEY,
  race_date DATE,
  venue VARCHAR,
  race_no INTEGER,
  race_name VARCHAR,
  surface VARCHAR,
  distance_m INTEGER,
  going VARCHAR,
  source_file VARCHAR
);
CREATE TABLE IF NOT EXISTS runners(
  race_id VARCHAR,
  horse_no INTEGER,
  horse_name VARCHAR,
  sex_age VARCHAR,
  jockey_name VARCHAR,
  weight_carried DOUBLE,
  odds DOUBLE,
  popularity INTEGER,
  finish_position INTEGER,
  finish_time VARCHAR,
  last3f DOUBLE,
  corner_order VARCHAR,
  source_file VARCHAR,
  PRIMARY KEY(race_id, horse_no)
);
"""

def connect(path="keiba.duckdb"):
    con = duckdb.connect(path)
    con.execute(SCHEMA)
    return con
