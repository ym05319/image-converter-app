import streamlit as st 
from PIL import Image
import io
import zipfile
import os

# ページ設定とスタイル（黒背景＋白文字）
st.set_page_config(page_title="画像変換ツール", layout="centered", page_icon="📷")
st.markdown("""
    <style>
        body, .block-container {
            background-color: black !important;
            color: white !important;
        }
        .stMarkdown, .stButton, .stDownloadButton, .stFileUploader, .stSelectbox label, .stCheckbox label {
            color: white !important;
        }
        .stDownloadButton > button {
            background-color: #333 !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# タイトルと説明
st.title("📷 画像変換ツール")
st.write("""
画像を高画質JPEGに変換します。
- 画像下部に注意文画像（shitaobiA.png）を統合するオプションあり。
- オプションで2MB以下に圧縮することも可能です。
- **合計アップロードサイズの目安：200MB以下を推奨**。
""")

# オプション設定
limit_size = st.checkbox("📏 画像サイズを2MB以下に制限する（画質は可能な限り維持）")
add_footer = st.checkbox("📎 注意文画像（shitaobiA.png）を下部に統合する")

# 注意文画像の読み込み
footer_path = "shitaobiA.png"
footer_img = None
if add_footer and os.path.exists(footer_path):
    footer_img = Image.open(footer_path).convert("RGB")
elif add_footer:
    st.warning("⚠ 注意文画像（shitaobiA.png）が見つかりません。アプリと同じフォルダに配置してください。")

# ファイルアップロード
uploaded_files = st.file_uploader(
    "画像ファイルをアップロードしてください（複数選択可）",
    type=["png", "bmp", "tiff", "jpeg", "jpg", "webp", "heic"],
    accept_multiple_files=True
)

# 画像変換処理
if uploaded_files:
    with st.spinner("画像を変換中..."):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for uploaded_file in uploaded_files:
                try:
                    img = Image.open(uploaded_file).convert("RGB")

                    # 注意文追加
                    if add_footer and footer_img:
                        footer_resized = footer_img.resize(
                            (img.width, int(footer_img.height * img.width / footer_img.width))
                        )
                        combined = Image.new("RGB", (img.width, img.height + footer_resized.height), (255, 255, 255))
                        combined.paste(img, (0, 0))
                        combined.paste(footer_resized, (0, img.height))
                        img = combined

                    # 初期JPEG保存（高画質）
                    quality = 95
                    final_img = img
                    img_buffer = io.BytesIO()
                    final_img.save(img_buffer, format="JPEG", quality=quality, optimize=True)

                    # サイズ制限ありの場合は圧縮処理
                    if limit_size:
                        max_bytes = 2 * 1024 * 1024
                        resize_factor = 1.0

                        while img_buffer.tell() > max_bytes and quality >= 60:
                            quality -= 5
                            img_buffer = io.BytesIO()
                            final_img.save(img_buffer, format="JPEG", quality=quality, optimize=True)

                        while img_buffer.tell() > max_bytes and resize_factor > 0.3:
                            resize_factor -= 0.1
                            new_size = (int(img.width * resize_factor), int(img.height * resize_factor))
                            final_img = img.resize(new_size)
                            img_buffer = io.BytesIO()
                            final_img.save(img_buffer, format="JPEG", quality=quality, optimize=True)

                    # 変換後のサイズ取得
                    final_size = img_buffer.tell()
                    out_name = os.path.splitext(uploaded_file.name)[0] + ".jpg"
                    zip_file.writestr(out_name, img_buffer.getvalue())

                    # プレビュー表示（全件）
                    st.image(final_img, caption=f"{out_name}（{round(final_size / 1024 / 1024, 2)} MB）", use_column_width=True)

                except Exception as e:
                    st.error(f"❌ {uploaded_file.name} の処理中にエラー: {e}")

        zip_buffer.seek(0)
        st.success("✅ 変換が完了しました。以下からZIPをダウンロードできます。")
        st.download_button(
            "📦 ZIPファイルをダウンロード",
            data=zip_buffer,
            file_name="変換済み画像.zip",
            mime="application/zip"
        )
