import streamlit as st
from PIL import Image
import io
import zipfile
import base64

# ページ設定とスタイル（黒背景・白文字）
st.set_page_config(page_title="画像変換ツール", layout="centered", page_icon="📷")
st.markdown("""
    <style>
        body, .block-container {
            background-color: black !important;
            color: white !important;
        }
        .stMarkdown, .stButton, .stDownloadButton, .stFileUploader, .stCheckbox label {
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
st.write("画像をJPG形式に変換します。必要に応じて2MB以下への圧縮や注意文画像の追加ができます。")

# オプション選択（どちらも任意）
limit_size = st.checkbox("画像サイズを2MB以下に制限する", value=False)
add_footer = st.checkbox("変換後の画像の下部に注意文画像を追加する", value=False)

# 2MB制限のバイト数
size_limit_bytes = 2 * 1024 * 1024

# 注意文画像（アプリ内埋め込み：base64形式で読み込む）
footer_img = None
if add_footer:
    try:
        footer_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAWgAAABLCAYAAABSPoaqAAAAAXNSR0IArs4c6QAAAARnQU1BAACx"
            "jwv8YQUAAA...（省略）..."
        )
        footer_img = Image.open(io.BytesIO(footer_data)).convert("RGB")
    except Exception:
        st.warning("⚠ 注意文画像の読み込みに失敗しました。")

# ファイルアップロード
uploaded_files = st.file_uploader(
    "画像ファイル（複数可）をここにドロップ、または「ファイルを選択」で選んでください",
    type=["png", "bmp", "tiff", "jpeg", "jpg", "webp", "heic"],
    accept_multiple_files=True
)

# 変換処理
if uploaded_files:
    with st.spinner("画像をJPGに変換中..."):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    img = Image.open(uploaded_file).convert("RGB")

                    # 下帯追加
                    if add_footer and footer_img:
                        footer_resized = footer_img.resize((img.width, int(footer_img.height * img.width / footer_img.width)))
                        combined = Image.new("RGB", (img.width, img.height + footer_resized.height), (255, 255, 255))
                        combined.paste(img, (0, 0))
                        combined.paste(footer_resized, (0, img.height))
                        img = combined

                    # 圧縮とリサイズ処理
                    quality = 95
                    resize_factor = 1.0
                    final_img = img
                    img_buffer = io.BytesIO()
                    final_img.save(img_buffer, format="JPEG", quality=quality)

                    if limit_size:
                        # 品質調整
                        while img_buffer.tell() > size_limit_bytes and quality >= 60:
                            quality -= 5
                            img_buffer = io.BytesIO()
                            final_img.save(img_buffer, format="JPEG", quality=quality)

                        # サイズ調整
                        while img_buffer.tell() > size_limit_bytes and resize_factor > 0.4:
                            resize_factor -= 0.1
                            new_size = (int(img.width * resize_factor), int(img.height * resize_factor))
                            final_img = img.resize(new_size)
                            img_buffer = io.BytesIO()
                            final_img.save(img_buffer, format="JPEG", quality=quality)

                    final_size = img_buffer.tell()
                    if limit_size and final_size > size_limit_bytes:
                        st.warning(f"⚠ {uploaded_file.name} は2MBに収まりませんでした（{round(final_size / 1024 / 1024, 2)}MB）")
                        continue

                    # ZIPに追加
                    out_name = os.path.splitext(uploaded_file.name)[0] + ".jpg"
                    zip_file.writestr(out_name, img_buffer.getvalue())

                    # プレビュー（最大10枚）
                    if i < 10:
                        st.image(final_img, caption=f"{out_name}（{round(final_size / 1024 / 1024, 2)}MB）", use_column_width=True)

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
