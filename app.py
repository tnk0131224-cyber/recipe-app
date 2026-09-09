import json
import re
from google import genai
import gspread
from PIL import Image
import streamlit as st

# 画面全体のタイトル設定
st.set_page_config(
    page_title="思考ゼロ！献立＆買い物アプリ", page_icon="🍳", layout="wide"
)

# --- 画面の見た目を整えるCSS ---
st.markdown(
    """
    <style>
    /* 画面全体の余白調整と横スクロール防止 */
    html, body, [data-testid="stAppViewContainer"] {
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }
    .main .block-container {
        padding-left: 0.4rem !important;
        padding-right: 0.4rem !important;
        padding-top: 1rem !important;
        max-width: 100% !important;
    }
    
    /* アコーディオンの背景と文字色を視認性の高いダーク調に修正 */
    div[data-testid="stExpander"] {
        border: 1px solid #4a5568 !important;
        border-radius: 8px !important;
        background-color: #1e293b !important;
        margin-bottom: 8px !important;
    }
    div[data-testid="stExpander"] summary p {
        font-size: 13px !important;
        font-weight: bold !important;
        color: #f8fafc !important;
    }
    /* アコーディオン内部のテキスト色を白に調整 */
    div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
        color: #f1f5f9 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🍳 思考ゼロ！献立＆買い物連携")

# --- 1. サイドバー設定 ---
st.sidebar.header("⚙️ アプリの設定")

default_api_key = st.secrets.get("GEMINI_API_KEY", "")
default_sheet_url = st.secrets.get("SPREADSHEET_URL", "")

api_key = st.sidebar.text_input(
    "Gemini API Key",
    value=default_api_key,
    type="password",
    help="Google AI Studioで取得したAPIキー",
)
sheet_url = st.sidebar.text_input(
    "スプレッドシートのURL",
    value=default_sheet_url,
    help="作成したスプレッドシートのブラウザURLを貼り付け",
)


# --- Google Sheets 接続関数 ---
@st.cache_resource
def init_gspread():
    if "gcp_service_account" in st.secrets:
        secret_val = st.secrets["gcp_service_account"]
        if isinstance(secret_val, str):
            creds_dict = json.loads(secret_val)
        else:
            creds_dict = dict(secret_val)
        return gspread.service_account_from_dict(creds_dict)
    else:
        return gspread.service_account(filename="service_account.json")


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
        "📌 レシピ保存",
        "📅 献立 ＆ 買い物リスト",
    ]
)

# ==========================================
# タブ1：SNSレシピのAI解析 ＆ 登録
# ==========================================
with tab1:
    st.subheader("SNSレシピをAIで解析して保存")

    uploaded_file = st.file_uploader(
        "レシピの画像（スクショ）", type=["png", "jpg", "jpeg"]
    )
    recipe_text = st.text_area(
        "またはテキスト/メモを貼り付け",
        height=90,
        placeholder="キャプション文面などをコピペ",
    )
    recipe_url = st.text_input(
        "レシピのURL（任意）",
        placeholder="https://vt.tiktok.com/... や https://instagram.com/...",
    )

    category = st.selectbox(
        "分類（カテゴリー）",
        ["メイン・肉", "メイン・魚", "メイン・麺", "メイン・その他", "サブ"],
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
                        model="gemini-3.6-flash", contents=contents
                    )
                    res_text = response.text

                    title_m = re.search(r"レシピ名:\s*(.*)", res_text)
                    title = (
                        title_m.group(1).strip() if title_m else "新しいレシピ"
                    )

                    ing_m = re.search(
                        r"材料:\s*([\s\S]*?)(?=手順:|$)", res_text
                    )
                    ingredients = (
                        ing_m.group(1).strip() if ing_m else res_text
                    )

                    steps_m = re.search(r"手順:\s*([\s\S]*)", res_text)
                    steps = steps_m.group(1).strip() if steps_m else ""

                    ws_library.append_row(
                        [
                            title,
                            category,
                            rating,
                            ingredients,
                            steps,
                            recipe_url.strip(),
                        ]
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
    st.link_button(
        "📊 スプレッドシートを開く", sheet_url, use_container_width=True
    )

    try:
        records = ws_library.get_all_records()
    except Exception as e:
        records = []
        st.error(f"ライブラリの読み込み失敗: {e}")

    if not records:
        st.info("まだライブラリにレシピが登録されていません。")
    else:
        selected_recipes = []
        summary_placeholder = st.empty()

        st.markdown("---")

        # --- 絞り込み ＆ ソート ---
        filter_cat = st.selectbox(
            "🔍 分類で絞り込み",
            [
                "すべて表示",
                "メイン・肉",
                "メイン・魚",
                "メイン・麺",
                "メイン・その他",
                "サブ",
            ],
        )

        sort_option = st.selectbox(
            "⇅ 並び替え（ソート）",
            [
                "分類順（肉→魚→麺...）",
                "評価が高い順",
                "登録順（新しい順）",
            ],
        )

        # データの整理とID付与
        processed_records = []
        for idx, rec in enumerate(records):
            item = dict(rec)
            item["_orig_idx"] = idx
            item["_row_num"] = idx + 2
            if filter_cat == "すべて表示" or item.get("分類") == filter_cat:
                processed_records.append(item)

        # ソート処理
        cat_order = {
            "メイン・肉": 1,
            "メイン・魚": 2,
            "メイン・麺": 3,
            "メイン・その他": 4,
            "サブ": 5,
        }
        rate_order = {"おいしかった！": 1, "普通": 2, "いまいち": 3}

        if sort_option == "分類順（肉→魚→麺...）":
            processed_records.sort(
                key=lambda x: cat_order.get(x.get("分類", ""), 99)
            )
        elif sort_option == "評価が高い順":
            processed_records.sort(
                key=lambda x: rate_order.get(x.get("評価", ""), 99)
            )
        elif sort_option == "登録順（新しい順）":
            processed_records.reverse()

        # メインとサブに分離
        main_list = [
            r
            for r in processed_records
            if str(r.get("分類", "")).startswith("メイン")
        ]
        sub_list = [
            r
            for r in processed_records
            if r.get("分類") == "サブ"
            or not str(r.get("分類", "")).startswith("メイン")
        ]


        # 1行描画用関数
        def render_recipe_row(rec):
            i = rec["_orig_idx"]
            row_num = rec["_row_num"]

            eval_icon = (
                "⭐"
                if rec.get("評価") == "おいしかった！"
                else ("🙂" if rec.get("評価") == "普通" else "🔺")
            )
            cat_tag = f"【{rec.get('分類', '他')}】"
            name = rec.get("レシピ名", f"レシピ{i+1}")
            url = str(rec.get("URL", "")).strip()
            has_link_mark = " 🔗" if url else ""

            col_c, col_a = st.columns([0.08, 0.92])

            with col_c:
                is_selected = st.checkbox(
                    "選択", key=f"select_{i}", label_visibility="collapsed"
                )
                if is_selected:
                    selected_recipes.append(rec)

            with col_a:
                badge = "✅ " if is_selected else ""
                label_text = f"{badge}{eval_icon}{cat_tag}{name}{has_link_mark}"

                with st.expander(label_text, expanded=False):
                    if url:
                        st.link_button(
                            "🔗 SNSで元のレシピを見る",
                            url,
                            use_container_width=True,
                        )
                        st.markdown("---")

                    edit_tab1, edit_tab2 = st.tabs(
                        ["📖 材料・作り方", "✏️ 修正・削除"]
                    )

                    with edit_tab1:
                        st.markdown(f"**【材料】**\n\n{rec.get('材料', '')}")
                        st.markdown(f"**【手順】**\n\n{rec.get('手順', '')}")

                    with edit_tab2:
                        st.caption("※修正して「保存」でシート更新")
                        new_title = st.text_input(
                            "レシピ名", value=name, key=f"edit_title_{i}"
                        )

                        categories = [
                            "メイン・肉",
                            "メイン・魚",
                            "メイン・麺",
                            "メイン・その他",
                            "サブ",
                        ]
                        current_cat_idx = (
                            categories.index(rec.get("分類"))
                            if rec.get("分類") in categories
                            else 0
                        )
                        new_cat = st.selectbox(
                            "分類",
                            categories,
                            index=current_cat_idx,
                            key=f"edit_cat_{i}",
                        )

                        ratings = ["いまいち", "普通", "おいしかった！"]
                        current_rate_idx = (
                            ratings.index(rec.get("評価"))
                            if rec.get("評価") in ratings
                            else 2
                        )
                        new_rate = st.selectbox(
                            "評価",
                            ratings,
                            index=current_rate_idx,
                            key=f"edit_rate_{i}",
                        )

                        new_ing = st.text_area(
                            "材料",
                            value=str(rec.get("材料", "")),
                            height=100,
                            key=f"edit_ing_{i}",
                        )
                        new_steps = st.text_area(
                            "手順",
                            value=str(rec.get("手順", "")),
                            height=80,
                            key=f"edit_steps_{i}",
                        )
                        new_url = st.text_input(
                            "URL", value=url, key=f"edit_url_{i}"
                        )

                        btn_col1, btn_col2 = st.columns([1, 1])
                        with btn_col1:
                            if st.button(
                                "💾 保存", key=f"save_{i}", type="primary"
                            ):
                                ws_library.update(
                                    range_name=f"A{row_num}:F{row_num}",
                                    values=[
                                        [
                                            new_title,
                                            new_cat,
                                            new_rate,
                                            new_ing,
                                            new_steps,
                                            new_url,
                                        ]
                                    ],
                                )
                                st.success("更新しました！")
                                st.rerun()

                        with btn_col2:
                            if st.button("🗑️ 削除", key=f"del_{i}"):
                                ws_library.delete_rows(row_num)
                                st.success("削除しました！")
                                st.rerun()


        # --- メイン料理セクション ---
        if main_list:
            with st.expander(
                f"🍖 メイン料理 ({len(main_list)}件)", expanded=True
            ):
                for rec in main_list:
                    render_recipe_row(rec)

        # --- サブ料理セクション ---
        if sub_list:
            with st.expander(
                f"🥗 サブ料理 ({len(sub_list)}件)", expanded=True
            ):
                for rec in sub_list:
                    render_recipe_row(rec)

        # --- サマリー更新 ---
        with summary_placeholder.container():
            if selected_recipes:
                st.success(
                    f"🛒 **今週の献立 ({len(selected_recipes)}件):** "
                    + " / ".join([r.get("レシピ名") for r in selected_recipes])
                )
            else:
                st.info("💡 チェックボックスで献立を選択してください。")

        st.markdown("---")
        st.subheader("🛒 買い物リスト出力")

        btn_create = st.button(
            "🛒 選んだ献立から「買い物リスト」を出力",
            type="primary",
            use_container_width=True,
        )

        if btn_create:
            if not selected_recipes:
                st.warning("レシピが選択されていません。")
            else:
                with st.spinner("売り場順の買い物リストを作成中..."):
                    combined_ingredients = "\n".join(
                        [
                            f"■ {r.get('レシピ名')}\n{r.get('材料')}"
                            for r in selected_rows := selected_recipes
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
                            model="gemini-3.6-flash", contents=prompt
                        )
                        lines = response.text.strip().split("\n")

                        rows_to_add = []
                        for line in lines:
                            line = line.strip().replace("`", "")
                            if "," in line:
                                parts = line.split(",", 1)
                                cat_name = parts[0].strip()
                                item_name = parts[1].strip()
                                rows_to_add.append([cat_name, item_name])

                        category_order = [
                            "野菜・果物",
                            "肉・魚",
                            "豆腐・納豆・加工食品",
                            "調味料・乾物・その他",
                        ]

                        def get_sort_key(row):
                            cat = row[0]
                            for idx, order_name in enumerate(category_order):
                                if order_name in cat:
                                    return idx
                            return len(category_order)

                        rows_to_add.sort(key=get_sort_key)

                        # B2:C1000 を綺麗にしてから書き込み
                        ws_shopping.batch_clear(["B2:C1000"])

                        if rows_to_add:
                            # 1. まずB・C列に新しい品目を流し込む
                            ws_shopping.append_rows(
                                rows_to_add, table_range="B2"
                            )

                            # 2. 追加された行数に合わせて、A列（チェックボックス）の既存のチェックをすべて「False（未チェック）」で一括リセットする
                            num_rows = len(rows_to_add)
                            false_values = [[False] for _ in range(num_rows)]
                            ws_shopping.update(
                                range_name=f"A2:A{2 + num_rows - 1}",
                                values=false_values,
                                value_input_option="USER_ENTERED",
                            )

                            st.success(
                                "🎉 スプレッドシートの「買い物リスト」を更新しました！（チェックも自動リセットされました）"
                            )
                            st.info(
                                "📱 スマホでGoogleスプレッドシートアプリを開いて買い物へGO！"
                            )
                        else:
                            st.write(response.text)

                    except Exception as e:
                        st.error(f"買い物リスト生成エラー: {e}")
