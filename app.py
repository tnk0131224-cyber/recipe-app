<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>レシピカード</title>
  <style>
    /* 全体スタイル */
    body {
      font-family: 'Helvetica Neue', Arial, 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', sans-serif;
      background-color: #f4f6f8;
      color: #333;
      padding: 20px;
    }

    .recipe-card {
      max-width: 600px;
      margin: 0 auto;
      background: #ffffff;
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
      overflow: hidden;
      border: 1px solid #e1e8ed;
    }

    .card-header {
      background-color: #2c3e50;
      color: #ffffff;
      padding: 16px 20px;
      font-size: 1.2rem;
      font-weight: bold;
    }

    .card-body {
      padding: 16px 20px;
    }

    /* アコーディオン共通スタイル */
    details {
      border: 1px solid #dcdfe6;
      border-radius: 8px;
      margin-bottom: 12px;
      background-color: #fafafa;
      transition: background-color 0.2s ease;
    }

    details[open] {
      background-color: #ffffff;
    }

    /* 横並びレイアウト（チェックボックス + タイトル） */
    summary {
      display: flex;
      align-items: center;
      padding: 12px 16px;
      cursor: pointer;
      font-weight: bold;
      color: #2c3e50;
      user-select: none;
      list-style: none; /* デフォルトの矢印を非表示 */
    }

    summary::-webkit-details-marker {
      display: none; /* Chrome/Safari用矢印非表示 */
    }

    summary:hover {
      background-color: #f0f4f8;
    }

    /* チェックボックスの配置 */
    .recipe-checkbox {
      width: 18px;
      height: 18px;
      margin-right: 12px;
      cursor: pointer;
      accent-color: #3498db;
    }

    /* 料理名テキスト */
    .recipe-title {
      flex-grow: 1;
      font-size: 1rem;
    }

    /* サブ料理用ラベルバッジ */
    .badge {
      font-size: 0.75rem;
      padding: 2px 8px;
      border-radius: 12px;
      margin-right: 8px;
      color: #fff;
    }
    .badge-main { background-color: #e67e22; }
    .badge-sub { background-color: #27ae60; }

    /* アコーディオン開閉矢印アイコン */
    .arrow-icon {
      font-size: 0.8rem;
      color: #7f8c8d;
      transition: transform 0.2s ease;
    }

    details[open] summary .arrow-icon {
      transform: rotate(90deg);
    }

    /* アコーディオン内部コンテンツ */
    .accordion-content {
      padding: 12px 16px 16px 46px; /* チェックボックスの位置と揃える調整 */
      border-top: 1px solid #eef1f6;
      font-size: 0.9rem;
      color: #555;
      line-height: 1.6;
    }

    .ingredient-list {
      margin: 0;
      padding-left: 20px;
    }
  </style>
</head>
<body>

<div class="recipe-card">
  <div class="card-header">
    今日の献立
  </div>

  <div class="card-body">
    
    <!-- 主菜のアコーディオン -->
    <details>
      <summary>
        <input type="checkbox" class="recipe-checkbox" id="check-main">
        <span class="badge badge-main">主菜</span>
        <span class="recipe-title">ハンバーグステーキ</span>
        <span class="arrow-icon">▶</span>
      </summary>
      <div class="accordion-content">
        <strong>【材料】</strong>
        <ul class="ingredient-list">
          <li>合挽き肉：300g</li>
          <li>玉ねぎ：1/2個</li>
          <li>パン粉：大さじ3</li>
        </ul>
      </div>
    </details>

    <!-- サブ料理1（副菜）のアコーディオン -->
    <details>
      <summary>
        <input type="checkbox" class="recipe-checkbox" id="check-sub1">
        <span class="badge badge-sub">副菜</span>
        <span class="recipe-title">彩り野菜のグリーンサラダ</span>
        <span class="arrow-icon">▶</span>
      </summary>
      <div class="accordion-content">
        <strong>【材料】</strong>
        <ul class="ingredient-list">
          <li>レタス：3枚</li>
          <li>ミニトマト：4個</li>
          <li>ドレッシング：適量</li>
        </ul>
      </div>
    </details>

    <!-- サブ料理2（スープ）のアコーディオン -->
    <details>
      <summary>
        <input type="checkbox" class="recipe-checkbox" id="check-sub2">
        <span class="badge badge-sub">汁物</span>
        <span class="recipe-title">具だくさんコンソメスープ</span>
        <span class="arrow-icon">▶</span>
      </summary>
      <div class="accordion-content">
        <strong>【材料】</strong>
        <ul class="ingredient-list">
          <li>コンソメ固形：1個</li>
          <li>キャベツ：1枚</li>
          <li>人参：1/4本</li>
        </ul>
      </div>
    </details>

  </div>
</div>

</body>
</html>
