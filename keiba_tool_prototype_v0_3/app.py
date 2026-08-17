
import os
from pathlib import Path
import pandas as pd
import streamlit as st
from src.db import connect
from src.loader import load_html_to_db

st.set_page_config(page_title="競馬分析ラボ", page_icon="🏇", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<style>
.block-container{max-width:1150px;padding-top:.7rem;padding-bottom:5rem}
div[data-testid="stMetric"]{
  background:rgba(255,255,255,.06);
  border:1px solid rgba(255,255,255,.10);
  border-radius:14px;
  padding:.75rem;
  color:inherit;
}
.stButton button{border-radius:12px}
@media(max-width:700px){
.block-container{padding-left:.65rem;padding-right:.65rem}
h1{font-size:1.5rem!important}
h2{font-size:1.15rem!important}
div[data-testid="stMetric"]{padding:.55rem}
}
</style>
""", unsafe_allow_html=True)

DB = os.getenv("KEIBA_DB_PATH","keiba.duckdb")
con = connect(DB)

def seed_demo():
    if con.execute("SELECT COUNT(*) FROM races").fetchone()[0] == 0:
        races = pd.read_csv("data/demo_races.csv")
        runners = pd.read_csv("data/demo_runners.csv")
        con.register("dr", races)
        con.execute("""
        INSERT INTO races
        SELECT race_id, CAST(race_date AS DATE), venue, race_no, race_name, surface, distance_m, going, 'demo'
        FROM dr
        """)
        runners["source_file"]="demo"
        con.register("du",runners)
        con.execute("""
        INSERT INTO runners
        SELECT race_id,horse_no,horse_name,sex_age,jockey_name,weight_carried,odds,popularity,
               finish_position,finish_time,last3f,corner_order,source_file
        FROM du
        """)

seed_demo()

st.title("競馬分析ラボ")
st.caption("試作 v0.3｜iPhone / PC対応")

home, search, horse, cond, import_tab = st.tabs(["ホーム","レース","馬分析","条件分析","取込"])

with home:
    n_race = con.execute("SELECT COUNT(*) FROM races").fetchone()[0]
    n_runner = con.execute("SELECT COUNT(*) FROM runners").fetchone()[0]
    years = con.execute("SELECT MIN(YEAR(race_date)), MAX(YEAR(race_date)) FROM races").fetchone()
    a,b,c = st.columns(3)
    a.metric("登録レース", f"{n_race:,}")
    b.metric("出走データ", f"{n_runner:,}")
    c.metric("期間", f"{years[0]}–{years[1]}")
    st.subheader("最近のレース")
    df=con.execute("""
      SELECT race_date,venue,race_no,race_name,surface,distance_m,race_id
      FROM races ORDER BY race_date DESC,race_no DESC LIMIT 20
    """).df()
    st.dataframe(df,hide_index=True,use_container_width=True)

with search:
    st.subheader("レース検索")
    years_df=con.execute("SELECT DISTINCT YEAR(race_date) y FROM races ORDER BY y DESC").df()
    year=st.selectbox("年",years_df.y.astype(int).tolist())
    c1,c2=st.columns(2)
    with c1:
        venue=st.selectbox("競馬場",["すべて","札幌","函館","福島","新潟","東京","中山","中京","京都","阪神","小倉"])
    with c2:
        surface=st.selectbox("馬場",["すべて","芝","ダート","障害"])
    where=["YEAR(race_date)=?"]; params=[year]
    if venue!="すべて": where.append("venue=?"); params.append(venue)
    if surface!="すべて": where.append("surface=?"); params.append(surface)
    q="SELECT race_date,venue,race_no,race_name,surface,distance_m,going,race_id FROM races WHERE "+" AND ".join(where)+" ORDER BY race_date DESC,race_no"
    df=con.execute(q,params).df()
    st.metric("該当",f"{len(df):,}レース")
    st.dataframe(df,hide_index=True,use_container_width=True)

with horse:
    st.subheader("馬分析")
    horses=con.execute("SELECT DISTINCT horse_name FROM runners WHERE horse_name IS NOT NULL ORDER BY horse_name").df()
    if horses.empty:
        st.info("馬データがありません")
    else:
        name=st.selectbox("馬名",horses.horse_name.tolist())
        df=con.execute("""
          SELECT r.race_date,r.venue,r.race_no,r.race_name,r.surface,r.distance_m,
                 ru.horse_no,ru.popularity,ru.odds,ru.finish_position,ru.last3f,ru.jockey_name
          FROM runners ru JOIN races r USING(race_id)
          WHERE ru.horse_name=?
          ORDER BY r.race_date DESC
        """,[name]).df()
        if not df.empty:
            a,b,c=st.columns(3)
            a.metric("出走",len(df))
            b.metric("勝率",f"{(df.finish_position.eq(1).mean()*100):.1f}%")
            c.metric("複勝率",f"{(df.finish_position.le(3).mean()*100):.1f}%")
            st.dataframe(df,hide_index=True,use_container_width=True)

with cond:
    st.subheader("条件分析")
    c1,c2=st.columns(2)
    with c1:
        venue=st.selectbox("競馬場 ",["すべて","札幌","函館","福島","新潟","東京","中山","中京","京都","阪神","小倉"])
        surface=st.selectbox("馬場 ",["すべて","芝","ダート","障害"])
    with c2:
        dmin,dmax=st.slider("距離",1000,3600,(1200,2000),100)
        omin,omax=st.slider("単勝オッズ",1.0,100.0,(1.0,20.0),0.5)
    where=["r.distance_m BETWEEN ? AND ?","ru.odds BETWEEN ? AND ?"]
    params=[dmin,dmax,omin,omax]
    if venue!="すべて": where.append("r.venue=?"); params.append(venue)
    if surface!="すべて": where.append("r.surface=?"); params.append(surface)
    q=f"""
      SELECT COUNT(*) n,
      AVG(CASE WHEN ru.finish_position=1 THEN 1 ELSE 0 END) win_rate,
      AVG(CASE WHEN ru.finish_position<=3 THEN 1 ELSE 0 END) place_rate,
      AVG(ru.odds) avg_odds
      FROM runners ru JOIN races r USING(race_id)
      WHERE {' AND '.join(where)}
    """
    n,w,p,o=con.execute(q,params).fetchone()
    a,b,c,d=st.columns(4)
    a.metric("対象頭数",f"{n:,}")
    b.metric("勝率","-" if w is None else f"{w*100:.1f}%")
    c.metric("複勝率","-" if p is None else f"{p*100:.1f}%")
    d.metric("平均オッズ","-" if o is None else f"{o:.1f}")
    st.caption("※ 回収率は払戻データ取込後に追加します。")

with import_tab:
    st.subheader("実レースHTMLを取り込む")
    st.write("netkeibaの結果HTMLをアップロードすると、レースと出走馬をDuckDBへ登録します。")
    uploads=st.file_uploader("HTMLファイル",type=["html","htm"],accept_multiple_files=True)
    if uploads and st.button("取り込む",use_container_width=True):
        ok=0; total=0
        for f in uploads:
            res=load_html_to_db(con,f)
            if res.get("ok"):
                ok+=1; total+=res.get("runners",0)
        st.success(f"{ok}レース、{total}頭を取り込みました。")
        st.rerun()

st.divider()
st.caption("v0.3：実HTML取込・DuckDB・検索・馬分析・条件分析の最小試作")
