import streamlit as st
from PIL import Image
import io
import zipfile
import os

# ページ設定とスタイル（黒背景・白文字）
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

# UI表示
st.title("📷 画像変換ツール")
st.write("画像をJPG形式に変換し、指定サイズ以下に圧縮します。")

# サイズ制限選択
size_option = st.selectbox("画像の最大サイズ（1枚あたり）を選択してください：", ["2MB", "4MB", "6MB"])
size_limit_bytes = int(size_option.replace("MB", "")) * 1024 * 1024

# 注意文統合の有無
add_footer = st.checkbox("変換後の画像の下部に注意文画像（shitaobiA.png）を追加する")

# 注意文画像のパス（Web用：アプリフォルダ直下）
footer_image_path = "shitaobiA.png"
footer_img = None
if os.path.exists(footer_image_path):
    footer_img = Image.open(footer_image_path).convert("RGB")
elif add_footer:
    st.warning("⚠ 注意文画像（shitaobiA.png）が見つかりません。GitHubリポジトリに配置してください。")

# ファイルアップロード
uploaded_files = st.file_uploader(
    "画像ファイル（複数可）をここにドロップ、または「ファイルを選択」で選んでください",
    type=["png", "bmp", "tiff", "jpeg", "jpg", "webp", "heic"],
    accept_multiple_files=True
)

# 変換処理
if uploaded_files:
    with st.spinner(f"画像をJPGに変換し、{size_option}以下に圧縮中..."):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    img = Image.open(uploaded_file).convert("RGB")

                    # 注意文を追加
                    if add_footer and footer_img:
                        footer_resized = footer_img.resize((img.width, int(footer_img.height * img.width / footer_img.width)))
                        combined = Image.new("RGB", (img.width, img.height + footer_resized.height), (255, 255, 255))
                        combined.paste(img, (0, 0))
                        combined.paste(footer_resized, (0, img.height))
                        img = combined

                    # 品質調整＋必要ならリサイズも
                    quality = 95
                    resize_factor = 1.0
                    final_img = img
                    img_buffer = io.BytesIO()
                    final_img.save(img_buffer, format="JPEG", quality=quality)

                    # 品質調整
                    while img_buffer.tell() > size_limit_bytes and quality >= 60:
                        quality -= 5
                        img_buffer = io.BytesIO()
                        final_img.save(img_buffer, format="JPEG", quality=quality)

                    # それでもサイズオーバーなら縮小
                    while img_buffer.tell() > size_limit_bytes and resize_factor > 0.4:
                        resize_factor -= 0.1
                        new_width = int(img.width * resize_factor)
                        new_height = int(img.height * resize_factor)
                        final_img = img.resize((new_width, new_height))
                        img_buffer = io.BytesIO()
                        final_img.save(img_buffer, format="JPEG", quality=quality)

                    # 最終サイズチェック
                    final_size = img_buffer.tell()
                    if final_size > size_limit_bytes:
                        st.warning(f"⚠ {uploaded_file.name} は制限サイズ内に収まりませんでした（{round(final_size / 1024 / 1024, 2)}MB）")
                        continue

                    # ZIP保存
                    out_name = os.path.splitext(uploaded_file.name)[0] + ".jpg"
                    zip_file.writestr(out_name, img_buffer.getvalue())

                    # 表示（最大10枚）
                    if i < 10:
                        st.image(final_img, caption=f"{out_name}（品質: {quality}）", use_column_width=True)

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
