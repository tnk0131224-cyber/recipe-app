import json
import re
from PIL import Image
import gspread
from google import genai
import streamlit as st

# 画面全体のタイトル設定
st.set_page_config(
    page_title="思考ゼロ！献立＆買い物アプリ", page_icon="🍳", layout="wide"
)

st.title("🍳 思考ゼロ！献立＆買い物リスト連携アプリ")

# --- 1. サイドバー設定 ---
st.sidebar.header("⚙️ アプリの設定")

# Secretsから自動取得（設定がなければ空文字）
default_api_key = st.secrets.get("GEMINI_API_KEY", "")
default_sheet_url = st.secrets.get("SPREADSHEET_URL", "")

api_key = st.sidebar.text_input(
    "Gemini API Key", value=default_api_key, type="password", help="Google AI Studioで取得したAPIキー"
)
sheet_url = st.sidebar.text_input(
    "スプレッドシートのURL",
    value=default_sheet_url,
    help="作成したスプレッドシートのブラウザURLを貼り付け",
)


# --- Google Sheets 接続関数 ---
@st.cache_resource
def init_gspread():
    # Streamlit CloudのSecrets（Web公開時）から読み込む場合
    if "gcp_service_account" in st.secrets:
        secret_val = st.secrets["gcp_service_account"]
        if isinstance(secret_val, str):
            creds_dict = json.loads(secret_val)
        else:
            creds_dict = dict(secret_val)
        return gspread.service_account_from_dict(creds_dict)
    # パソコン（ローカル環境）の service_account.json から読み込む場合
    else:
        return gspread.service_account(filename="service_account.json")


# 必須入力チェック
if not api_key or not sheet_url:
    st.info(
        "👈 左側のサイドバーに「Gemini API Key」と「スプレッドシートURL」を入力してください。"
    )
    st.stop()

try:
    client = genai.Client(api_key=api_key)
    gc = init_gspread()
    sh = gc.open_by_url(sheet_url)
    ws_library = sh.worksheet("献立ライブラリ")
    ws_shopping = sh.worksheet("買い物リスト")
except Exception as e:
    st.error(f"接続エラーが発生しました: {e}")
    st.stop()

# --- メイン画面（タブ切り替え） ---
tab1, tab2 = st.tabs(
    [
        "📌 1. レシピの解析・ライブラリ保存",
        "📅 2. 献立えらび ＆ 買い物リスト作成",
    ]
)

# ==========================================
# タブ1：SNSレシピのAI解析 ＆ 登録
# ==========================================
with tab1:
    st.subheader("SNSレシピをAIで解析して保存")
    st.caption(
        "画像（スクショ）またはテキストを入力すると、AIが「レシピ名・材料・手順」を自動抽出します。"
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_file = st.file_uploader(
            "レシピの画像（スクショ）", type=["png", "jpg", "jpeg"]
        )
        recipe_text = st.text_area(
            "またはテキスト/メモを貼り付け",
            height=120,
            placeholder="キャプション文面などをコピペ",
        )

    with col2:
        category = st.selectbox(
            "分類（カテゴリー）",
            ["レンジだけ", "フライパン1つ", "包丁いらず", "作り置き・時短", "その他"],
        )
        rating = st.select_slider(
            "家族の評判・評価",
            options=["いまいち", "普通", "おいしかった！"],
            value="おいしかった！",
        )

    if st.button("🚀 レシピを解析してライブラリに追加", type="primary"):
        if not uploaded_file and not recipe_text:
            st.warning("画像またはテキストを入力してください。")
        else:
            with st.spinner("AIがレシピを解析中..."):
                prompt = """
                提供された情報からレシピ情報を抽出し、以下のフォーマット厳守で出力してください。
                余計な挨拶や記号は不要です。

                レシピ名: (料理名)
                材料: (材料と分量を改行区切りで)
                手順: (超簡略化した3ステップ以内の手順)
                """

                contents = [prompt]
                if recipe_text:
                    contents.append(f"テキスト情報:\n{recipe_text}")
                if uploaded_file:
                    contents.append(Image.open(uploaded_file))

                try:
                    response = client.models.generate_content(
                        model="gemini-2.0-flash", contents=contents
                    )
                    res_text = response.text

                    # 正規表現で各要素を抽出
                    title_m = re.search(r"レシピ名:\s*(.*)", res_text)
                    title = title_m.group(1).strip() if title_m else "新しいレシピ"

                    ing_m = re.search(
                        r"材料:\s*([\s\S]*?)(?=手順:|$)", res_text
                    )
                    ingredients = (
                        ing_m.group(1).strip() if ing_m else res_text
                    )

                    steps_m = re.search(r"手順:\s*([\s\S]*)", res_text)
                    steps = steps_m.group(1).strip() if steps_m else ""

                    # スプレッドシート「献立ライブラリ」の末尾に追加
                    # 列構成: A:レシピ名, B:分類, C:評価, D:材料, E:手順
                    ws_library.append_row(
                        [title, category, rating, ingredients, steps]
                    )

                    st.success(
                        f"✅ 『{title}』を献立ライブラリに保存しました！"
                    )
                    st.expander("抽出結果を確認").write(res_text)

                except Exception as e:
                    st.error(f"解析エラー: {e}")

# ==========================================
# タブ2：ライブラリから選択 ＆ 買い物リスト出力
# ==========================================
with tab2:
    st.subheader("今週作るレシピを選んで買い物リストを作成")

    try:
        records = ws_library.get_all_records()
    except Exception as e:
        records = []
        st.error(f"ライブラリの読み込み失敗: {e}")

    if not records:
        st.info(
            "まだライブラリにレシピが登録されていません。タブ1から登録してください。"
        )
    else:
        st.write("▼ 作りたいレシピの「この献立を今週作る！」にチェックを入れてください")

        selected_recipes = []

        for i, rec in enumerate(records):
            eval_icon = (
                "⭐"
                if rec.get("評価") == "おいしかった！"
                else ("🙂" if rec.get("評価") == "普通" else "🔺")
            )
            cat_tag = f"【{rec.get('分類', 'その他')}】"
            name = rec.get("レシピ名", f"レシピ{i+1}")

            label = f"{eval_icon} {cat_tag} {name}"

            with st.expander(label):
                st.write(f"**材料:**\n{rec.get('材料', '')}")
                st.write(f"**手順:**\n{rec.get('手順', '')}")
                if st.checkbox("この献立を今週作る！", key=f"select_{i}"):
                    selected_recipes.append(rec)

        st.markdown("---")

        if st.button(
            "🛒 選んだ献立から「買い物リスト」をスプレッドシートに出力",
            type="primary",
        ):
            if not selected_recipes:
                st.warning("レシピが選択されていません。")
            else:
                with st.spinner("売り場順の買い物リストを作成中..."):
                    combined_ingredients = "\n".join(
                        [
                            f"■ {r.get('レシピ名')}\n{r.get('材料')}"
                            for r in selected_recipes
                        ]
                    )

                    prompt = f"""
                    以下の複数レシピの材料一覧を統合し、重複食材をまとめて、スーパーで買い回りやすい「売り場順」に整理してください。

                    出力形式は、CSV風（カンマ区切り、ヘッダー無し）で1行につき「売り場カテゴリ,品目と数量」を出力してください。

                    売り場カテゴリ例:
                    - 野菜・果物
                    - 肉・魚
                    - 豆腐・納豆・加工食品
                    - 調味料・乾物・その他

                    材料一覧:
                    {combined_ingredients}
                    """

                    try:
                        response = client.models.generate_content(
                            model="gemini-2.0-flash", contents=prompt
                        )
                        lines = response.text.strip().split("\n")

                        # 買い物リストシートを一旦全クリア
                        ws_shopping.clear()
                        # 1行目にヘッダーを書き込み
                        ws_shopping.append_row(["チェック", "売り場", "品目"])

                        rows_to_add = []
                        for line in lines:
                            line = line.strip().replace("`", "")
                            if "," in line:
                                parts = line.split(",", 1)
                                cat_name = parts[0].strip()
                                item_name = parts[1].strip()
                                # A列: False (チェックボックス用), B列: 売り場, C列: 品目
                                rows_to_add.append([False, cat_name, item_name])

                        if rows_to_add:
                            ws_shopping.append_rows(rows_to_add)
                            st.success(
                                "🎉 スプレッドシートの「買い物リスト」を更新しました！"
                            )
                            st.info(
                                "📱 スマホでGoogleスプレッドシートアプリを開いて買い物へGO！"
                            )
                        else:
                            st.write(response.text)

                    except Exception as e:
                        st.error(f"買い物リスト生成エラー: {e}")
