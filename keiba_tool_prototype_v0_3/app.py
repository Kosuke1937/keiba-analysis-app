import os
import pandas as pd
import streamlit as st
from src.db import connect
from src.loader import load_html_to_db

st.set_page_config(
    page_title="競馬分析ラボ",
    page_icon="🏇",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container{max-width:1150px;padding-top:.8rem;padding-bottom:5rem}
[data-testid="stMetric"]{
  border:1px solid rgba(128,128,128,.28);
  border-radius:14px;
  padding:.75rem;
  background:rgba(128,128,128,.08);
}
[data-testid="stMetricLabel"],[data-testid="stMetricValue"]{color:inherit!important}
.stButton button{border-radius:12px}
.status-box{border:1px solid rgba(128,128,128,.28);border-radius:14px;padding:.8rem 1rem;margin:.25rem 0 1rem 0}
.small-note{opacity:.72;font-size:.88rem}
@media(max-width:700px){
 .block-container{padding-left:.7rem;padding-right:.7rem}
 h1{font-size:1.55rem!important;margin-bottom:.15rem!important}
 h2{font-size:1.25rem!important}
 h3{font-size:1.08rem!important}
 [data-testid="stMetric"]{padding:.58rem}
 [data-testid="stMetricValue"]{font-size:1.65rem!important}
 .stTabs [data-baseweb="tab"]{padding-left:.65rem;padding-right:.65rem}
}
</style>
""", unsafe_allow_html=True)

DB = os.getenv("KEIBA_DB_PATH", "keiba.duckdb")
con = connect(DB)


def seed_demo():
    if con.execute("SELECT COUNT(*) FROM races").fetchone()[0] == 0:
        races = pd.read_csv("data/demo_races.csv")
        runners = pd.read_csv("data/demo_runners.csv")
        con.register("dr", races)
        con.execute("""
        INSERT INTO races
        SELECT race_id, CAST(race_date AS DATE), venue, race_no, race_name,
               surface, distance_m, going, 'demo'
        FROM dr
        """)
        runners["source_file"] = "demo"
        con.register("du", runners)
        con.execute("""
        INSERT INTO runners
        SELECT race_id,horse_no,horse_name,sex_age,jockey_name,weight_carried,
               odds,popularity,finish_position,finish_time,last3f,corner_order,source_file
        FROM du
        """)


def data_status():
    n_race = con.execute("SELECT COUNT(*) FROM races").fetchone()[0]
    n_runner = con.execute("SELECT COUNT(*) FROM runners").fetchone()[0]
    demo_race = con.execute("SELECT COUNT(*) FROM races WHERE source_file='demo'").fetchone()[0]
    real_race = n_race - demo_race
    return n_race, n_runner, demo_race, real_race


def import_races_csv(upload):
    df = pd.read_csv(upload)
    cols = ["race_id","race_date","venue","race_no","race_name","surface","distance_m","going"]
    missing = set(cols) - set(df.columns)
    if missing:
        raise ValueError("不足列: " + ", ".join(sorted(missing)))
    x = df[cols].copy()
    x["source_file"] = getattr(upload, "name", "uploaded_races.csv")
    con.register("race_csv_in", x)
    con.execute("""
      INSERT OR REPLACE INTO races
      SELECT CAST(race_id AS VARCHAR), CAST(race_date AS DATE), venue,
             CAST(race_no AS INTEGER), race_name, surface,
             CAST(distance_m AS INTEGER), going, source_file
      FROM race_csv_in
    """)
    return len(x)


def import_runners_csv(upload):
    df = pd.read_csv(upload)
    cols = [
        "race_id","horse_no","horse_name","sex_age","jockey_name","weight_carried",
        "odds","popularity","finish_position","finish_time","last3f","corner_order"
    ]
    missing = set(cols) - set(df.columns)
    if missing:
        raise ValueError("不足列: " + ", ".join(sorted(missing)))
    x = df[cols].copy()
    x["source_file"] = getattr(upload, "name", "uploaded_runners.csv")
    con.register("runner_csv_in", x)
    con.execute("""
      INSERT OR REPLACE INTO runners
      SELECT CAST(race_id AS VARCHAR), CAST(horse_no AS INTEGER), horse_name, sex_age,
             jockey_name, CAST(weight_carried AS DOUBLE), CAST(odds AS DOUBLE),
             CAST(popularity AS INTEGER), CAST(finish_position AS INTEGER),
             CAST(finish_time AS VARCHAR), CAST(last3f AS DOUBLE),
             CAST(corner_order AS VARCHAR), source_file
      FROM runner_csv_in
    """)
    return len(x)


seed_demo()

st.title("競馬分析ラボ")
st.caption("試作 v0.4｜iPhone / PC対応")

n_race, n_runner, demo_race, real_race = data_status()
if real_race == 0:
    st.markdown(
        '<div class="status-box"><b>現在はデモデータ表示です。</b><br>'
        '<span class="small-note">Google Driveの実データ接続を順次進めています。分析画面の操作確認用として5レースを入れています。</span></div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f'<div class="status-box"><b>実データ接続中</b><br>'
        f'<span class="small-note">実レース {real_race:,}件 / デモ {demo_race:,}件</span></div>',
        unsafe_allow_html=True,
    )

home, search, horse, cond, data_tab = st.tabs(["ホーム","レース","馬分析","条件分析","データ"])

with home:
    n_race, n_runner, demo_race, real_race = data_status()
    years = con.execute("SELECT MIN(YEAR(race_date)), MAX(YEAR(race_date)) FROM races").fetchone()
    a,b,c = st.columns(3)
    a.metric("登録レース", f"{n_race:,}")
    b.metric("出走データ", f"{n_runner:,}")
    c.metric("期間", f"{years[0]}–{years[1]}")
    st.subheader("最近のレース")
    df = con.execute("""
      SELECT race_date, venue, race_no, race_name, surface, distance_m, race_id
      FROM races ORDER BY race_date DESC, race_no DESC LIMIT 20
    """).df()
    st.dataframe(df, hide_index=True, use_container_width=True)

with search:
    st.subheader("レース検索")
    years_df = con.execute("SELECT DISTINCT YEAR(race_date) y FROM races ORDER BY y DESC").df()
    year = st.selectbox("年", years_df.y.astype(int).tolist())
    c1,c2 = st.columns(2)
    with c1:
        venue = st.selectbox("競馬場", ["すべて","札幌","函館","福島","新潟","東京","中山","中京","京都","阪神","小倉"])
    with c2:
        surface = st.selectbox("馬場", ["すべて","芝","ダート","障害"])
    where = ["YEAR(race_date)=?"]
    params = [year]
    if venue != "すべて":
        where.append("venue=?")
        params.append(venue)
    if surface != "すべて":
        where.append("surface=?")
        params.append(surface)
    q = "SELECT race_date,venue,race_no,race_name,surface,distance_m,going,race_id FROM races WHERE " + " AND ".join(where) + " ORDER BY race_date DESC,race_no"
    df = con.execute(q, params).df()
    st.metric("該当", f"{len(df):,}レース")
    st.dataframe(df, hide_index=True, use_container_width=True)

with horse:
    st.subheader("馬分析")
    horses = con.execute("SELECT DISTINCT horse_name FROM runners WHERE horse_name IS NOT NULL ORDER BY horse_name").df()
    if horses.empty:
        st.info("馬データがありません。")
    else:
        name = st.selectbox("馬名", horses.horse_name.tolist())
        df = con.execute("""
          SELECT r.race_date,r.venue,r.race_no,r.race_name,r.surface,r.distance_m,
                 ru.horse_no,ru.popularity,ru.odds,ru.finish_position,ru.last3f,ru.jockey_name
          FROM runners ru JOIN races r USING(race_id)
          WHERE ru.horse_name=? ORDER BY r.race_date DESC
        """, [name]).df()
        if not df.empty:
            a,b,c = st.columns(3)
            a.metric("出走", len(df))
            b.metric("勝率", f"{df.finish_position.eq(1).mean()*100:.1f}%")
            c.metric("複勝率", f"{df.finish_position.le(3).mean()*100:.1f}%")
            st.dataframe(df, hide_index=True, use_container_width=True)

with cond:
    st.subheader("条件分析")
    c1,c2 = st.columns(2)
    with c1:
        venue = st.selectbox("競馬場 ", ["すべて","札幌","函館","福島","新潟","東京","中山","中京","京都","阪神","小倉"])
        surface = st.selectbox("馬場 ", ["すべて","芝","ダート","障害"])
    with c2:
        dmin,dmax = st.slider("距離", 1000, 3600, (1200,2000), 100)
        omin,omax = st.slider("単勝オッズ", 1.0, 100.0, (1.0,20.0), 0.5)
    where = ["r.distance_m BETWEEN ? AND ?", "ru.odds BETWEEN ? AND ?"]
    params = [dmin,dmax,omin,omax]
    if venue != "すべて":
        where.append("r.venue=?")
        params.append(venue)
    if surface != "すべて":
        where.append("r.surface=?")
        params.append(surface)
    q = f"""
      SELECT COUNT(*) n,
      AVG(CASE WHEN ru.finish_position=1 THEN 1 ELSE 0 END) win_rate,
      AVG(CASE WHEN ru.finish_position<=3 THEN 1 ELSE 0 END) place_rate,
      AVG(ru.odds) avg_odds
      FROM runners ru JOIN races r USING(race_id)
      WHERE {' AND '.join(where)}
    """
    n,w,p,o = con.execute(q, params).fetchone()
    a,b,c,d = st.columns(4)
    a.metric("対象頭数", f"{n:,}")
    b.metric("勝率", "-" if w is None else f"{w*100:.1f}%")
    c.metric("複勝率", "-" if p is None else f"{p*100:.1f}%")
    d.metric("平均オッズ", "-" if o is None else f"{o:.1f}")
    st.caption("※ 回収率は払戻データ取込後に追加します。")

with data_tab:
    st.subheader("データ取込")
    st.write("今後Google Driveから自動同期します。現時点ではCSVまたはnetkeiba結果HTMLを直接取り込めます。")
    csv1, csv2 = st.columns(2)
    with csv1:
        st.markdown("#### レースCSV")
        races_upload = st.file_uploader("races CSV", type=["csv"], key="races_csv")
        st.caption("race_id, race_date, venue, race_no, race_name, surface, distance_m, going")
        if races_upload and st.button("レースCSVを取込", use_container_width=True):
            try:
                n = import_races_csv(races_upload)
                st.success(f"{n:,}レースを登録しました。")
                st.rerun()
            except Exception as e:
                st.error(str(e))
    with csv2:
        st.markdown("#### 出走CSV")
        runners_upload = st.file_uploader("runners CSV", type=["csv"], key="runners_csv")
        st.caption("race_id, horse_no, horse_name, jockey_name, odds, popularity, finish_position など")
        if runners_upload and st.button("出走CSVを取込", use_container_width=True):
            try:
                n = import_runners_csv(runners_upload)
                st.success(f"{n:,}頭を登録しました。")
                st.rerun()
            except Exception as e:
                st.error(str(e))
    st.divider()
    st.markdown("#### netkeiba結果HTML")
    uploads = st.file_uploader("HTMLファイル", type=["html","htm"], accept_multiple_files=True)
    if uploads and st.button("HTMLを取り込む", use_container_width=True):
        ok = 0
        total = 0
        for f in uploads:
            res = load_html_to_db(con, f)
            if res.get("ok"):
                ok += 1
                total += res.get("runners", 0)
        st.success(f"{ok}レース、{total}頭を取り込みました。")
        st.rerun()
    st.divider()
    n_race, n_runner, demo_race, real_race = data_status()
    st.markdown("#### 現在のDB")
    st.write(f"実レース: **{real_race:,}** / デモ: **{demo_race:,}** / 出走: **{n_runner:,}**")
    st.caption("注意：Streamlit Community Cloud上のDuckDBは再起動で消える可能性があります。永続化はGoogle Drive自動同期またはクラウドDB化で対応します。")

st.divider()
st.caption("v0.4：モバイルUI改善・CSV一括取込・実データ接続準備")
