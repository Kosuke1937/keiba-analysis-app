
# 競馬分析ラボ v0.3

一旦触って評価するための試作版です。

## できること
- iPhone/PC向けレスポンシブ画面
- DuckDBにレース・出走馬を保存
- 年/競馬場/芝ダートでレース検索
- 馬ごとの過去成績
- 条件別の勝率・複勝率
- netkeiba結果HTMLをアップロードして取込
- デモデータ付きなので、実データがなくても起動確認可能

## 起動
```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

## iPhone単体で使うには
このフォルダをGitHubへ置き、Streamlit Community Cloud等へデプロイすると固定URLで利用できます。

現時点ではGoogle Drive自動同期は未実装です。
最初は「Google Drive → HTMLアップロード → DuckDB」でUI/分析価値を確認し、
次版でDrive自動同期を追加します。

## 次に足すもの
1. Google Drive自動同期
2. 過去5年の全レース取込
3. 払戻 → 単勝/複勝回収率
4. 馬場・クラス・枠・脚質・騎手・血統の条件分析
5. AI予測・期待値
6. お気に入り条件
