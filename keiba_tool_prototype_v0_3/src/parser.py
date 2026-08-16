
from pathlib import Path
import re
import pandas as pd
from bs4 import BeautifulSoup

RACE_ID_RE = re.compile(r"(20\d{10})")
DATE_RE = re.compile(r"(20\d{2})年(\d{1,2})月(\d{1,2})日")
DIST_RE = re.compile(r"(芝|ダート|障害)\s*(\d{3,4})m")

def _clean_cols(df):
    df = df.copy()
    df.columns = [
        str(c[0] if isinstance(c, tuple) else c).replace("\n","").strip()
        for c in df.columns
    ]
    return df

def parse_result_html(path_or_file):
    if hasattr(path_or_file, "read"):
        raw = path_or_file.read()
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="ignore")
        source = getattr(path_or_file, "name", "uploaded.html")
    else:
        source = str(path_or_file)
        raw = Path(path_or_file).read_text(encoding="utf-8", errors="ignore")

    soup = BeautifulSoup(raw, "lxml")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    og = soup.find("meta", attrs={"property":"og:description"})
    desc = og.get("content","") if og else ""
    text = " ".join([title, desc])

    rid_match = RACE_ID_RE.search(raw) or RACE_ID_RE.search(source)
    race_id = rid_match.group(1) if rid_match else None

    d = DATE_RE.search(text)
    race_date = f"{d.group(1)}-{int(d.group(2)):02d}-{int(d.group(3)):02d}" if d else None

    venue = None
    for v in ["札幌","函館","福島","新潟","東京","中山","中京","京都","阪神","小倉"]:
        if v in text:
            venue = v
            break

    rno = None
    m = re.search(r"(\d{1,2})R", text)
    if m:
        rno = int(m.group(1))
    elif race_id:
        rno = int(race_id[-2:])

    surface, distance = None, None
    dm = DIST_RE.search(raw)
    if dm:
        surface, distance = dm.group(1), int(dm.group(2))

    race_name = None
    if desc:
        m = re.search(r"\d+R\s+(.+?)の結果", desc)
        if m:
            race_name = m.group(1).strip()

    race = {
        "race_id": race_id, "race_date": race_date, "venue": venue,
        "race_no": rno, "race_name": race_name, "surface": surface,
        "distance_m": distance, "going": None, "source_file": source
    }

    runners = None
    try:
        tables = pd.read_html(raw)
    except Exception:
        tables = []

    for df in tables:
        df = _clean_cols(df)
        cols = set(df.columns)
        # netkeiba result table usually contains several of these.
        score = sum(c in cols for c in ["着順","馬番","馬名","性齢","斤量","騎手","タイム","単勝","人気","上り"])
        if score >= 4:
            runners = df
            break

    if runners is None:
        return race, pd.DataFrame()

    rename = {}
    for c in runners.columns:
        if c == "着順": rename[c] = "finish_position"
        elif c == "馬番": rename[c] = "horse_no"
        elif c == "馬名": rename[c] = "horse_name"
        elif c == "性齢": rename[c] = "sex_age"
        elif c == "騎手": rename[c] = "jockey_name"
        elif c == "斤量": rename[c] = "weight_carried"
        elif c in ["単勝","オッズ"]: rename[c] = "odds"
        elif c == "人気": rename[c] = "popularity"
        elif c == "タイム": rename[c] = "finish_time"
        elif c in ["上り","上がり"]: rename[c] = "last3f"
        elif c in ["通過","コーナー通過順位"]: rename[c] = "corner_order"
    runners = runners.rename(columns=rename)

    wanted = ["finish_position","horse_no","horse_name","sex_age","jockey_name",
              "weight_carried","odds","popularity","finish_time","last3f","corner_order"]
    for c in wanted:
        if c not in runners.columns:
            runners[c] = None
    runners = runners[wanted].copy()
    runners["race_id"] = race_id
    runners["source_file"] = source

    for c in ["finish_position","horse_no","popularity"]:
        runners[c] = pd.to_numeric(runners[c], errors="coerce").astype("Int64")
    for c in ["weight_carried","odds","last3f"]:
        runners[c] = pd.to_numeric(runners[c], errors="coerce")

    return race, runners
