

# 主應用程式 (app.py)
import streamlit as st
from streamlit_drawable_canvas import st_canvas
import numpy as np
from PIL import Image, ImageOps
import time
import random
import streamlit.components.v1 as components

# 匯入自訂模組
from model import load_ai_model, predict_image
from app_utils import preprocess_image
from fish_animation import FishTank

# --- 1. 頁面設定與資源載入 ---
st.set_page_config(
    page_title="AI 互動魚缸",
    page_icon="🐠",
    layout="wide"
)

# 注入 CSS 來改變 icon 顏色
st.markdown("""
<style>
/* 讓 streamlit-drawable-canvas 工具列的所有 icon 更顯眼 */
div[data-testid="stDrawableCanvasToolbar"] button svg {
    fill: #333333 !important; /* 設定為深灰色以增加可見度 */
}

/* 針對刪除按鈕 icon，維持紅色 */
div[data-testid="stDrawableCanvasToolbar"] button:last-child svg {
    fill: red !important;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_model():
    """載入並快取 AI 模型"""
    return load_ai_model()

model = get_model()

# 初始化 session_state
if "tank" not in st.session_state:
    st.session_state.tank = FishTank(width=560, height=560)
if "canvas_key" not in st.session_state:
    st.session_state.canvas_key = f"canvas_{random.randint(0, 1000)}"
if "last_prediction_info" not in st.session_state:
    st.session_state.last_prediction_info = None

# --- 2. 輔助函式：處理使用者繪製的魚 ---
def crop_and_prepare_sprite(image_data: np.ndarray) -> Image:
    """
    將使用者在畫布上畫的圖案去背、裁切並縮放，製成魚的圖片。
    使用 NumPy 進行高效處理。
    """
    if image_data is None or image_data.shape[2] < 4 or np.all(image_data[:, :, 3] == 0):
        return None # 畫布是空的

    # 尋找邊界框
    alpha = image_data[:, :, 3]
    non_transparent_coords = np.argwhere(alpha > 0)
    if non_transparent_coords.size == 0:
        return None
    
    y_min, x_min = non_transparent_coords.min(axis=0)
    y_max, x_max = non_transparent_coords.max(axis=0)

    # 裁切圖片
    cropped_data = image_data[y_min:y_max+1, x_min:x_max+1]

    # 將接近白色的像素變為透明
    pixels = cropped_data.copy()
    white_threshold = 245
    is_white = (pixels[:, :, 0] > white_threshold) & \
               (pixels[:, :, 1] > white_threshold) & \
               (pixels[:, :, 2] > white_threshold)
    
    pixels[is_white, 3] = 0 # 將 alpha 通道設為 0

    # 從 NumPy 陣列建立 PIL 圖片
    final_sprite = Image.fromarray(pixels, 'RGBA')

    # 縮放圖片到適合的大小，保持長寬比
    final_sprite.thumbnail((120, 120), Image.Resampling.LANCZOS)
    
    return final_sprite

# --- 3. 主標題與介紹 ---
st.title("🎨 AI 互動魚缸：畫魚成真！")
st.markdown("歡迎來到 AI 互動魚缸！在這裡，您畫的魚將會被 AI 辨識，如果成功，您親手畫的魚就會在魚缸裡游動起來。")

# --- 4. 主要佈局 (分為左右兩欄) ---
col1, col2 = st.columns([1, 1])

# --- 4.1. 左欄：繪圖區與控制項 ---
with col1:
    st.header("步驟 1: 揮灑創意畫隻魚")

    with st.container():
        st.write("**繪圖工具**")
        tool_col1, tool_col2 = st.columns([1, 1])
        
        stroke_color = tool_col1.color_picker("畫筆顏色:", "#000000")
        stroke_width = tool_col2.slider("畫筆粗細:", 1, 50, 20)
        st.info("💡 提示：將顏色選為白色即可當作橡皮擦。魚頭請向右畫")

    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="#FFFFFF",
        height=400,
        width=560,
        drawing_mode="freedraw",
        key=st.session_state.canvas_key,
    )

    # 將辨識結果區塊移到按鈕上方，並使用 session_state 來顯示
    st.header("步驟 2: AI 的思考過程")
    if st.session_state.last_prediction_info:
        info = st.session_state.last_prediction_info
        with st.expander("點擊查看 AI 如何辨識您的畫作", expanded=True):
            step_col1, step_col2, step_col3 = st.columns(3)
            step_col1.image(info["image_data"], caption="1. 您的原始畫作", use_column_width=True)
            step_col2.image(info["img_array_28x28"], caption="2. AI 所見的樣子 (28x28)", use_column_width=True)
            step_col3.metric("3. 辨識結果", "是魚！🐟" if info["is_fish"] else "不是魚 ❌", f"{info['confidence']:.0%} 信心")
        
        # 根據上次的辨識結果顯示訊息
        if info["is_fish"]:
            st.success("太棒了！AI 認為這是一隻魚，已將牠放進魚缸。")
        else:
            st.error("嗯... AI 覺得這不太像魚。沒關係，再試一次，或調整您的畫作！")
    else:
        st.info("畫完魚後，點擊下方的「AI 魔法辨識」按鈕，這裡會顯示辨識結果。")


    if st.button("✨ AI 魔法辨識", type="primary", use_container_width=True):
        if model is None:
            st.error("模型載入失敗，請檢查 `fish_classifier.h5` 檔案。")
        elif canvas_result.image_data is not None:
            img_array_28x28 = preprocess_image(canvas_result.image_data)
            is_fish, confidence = predict_image(img_array_28x28, model)

            # 將最新的辨識結果存入 session_state
            st.session_state.last_prediction_info = {
                "image_data": canvas_result.image_data,
                "img_array_28x28": img_array_28x28,
                "is_fish": is_fish,
                "confidence": confidence
            }
            
            if is_fish:
                fish_sprite = crop_and_prepare_sprite(canvas_result.image_data)
                if fish_sprite:
                    st.session_state.tank.add_fish(fish_sprite)
                    # 清空畫布以便畫下一隻
                    st.session_state.canvas_key = f"canvas_{random.randint(0, 1000)}"
                else:
                    st.warning("無法從畫布中提取有效的圖案，請再畫一次。")
            
            # Rerun để立即更新介面顯示結果
            st.experimental_rerun()
        else:
            st.warning("您還沒有畫任何東西喔！")

# --- 4.2. 右欄：魚缸動畫區 ---
with col2:
    st.header("步驟 3: 欣賞您的魚缸")

    # 永遠渲染魚缸，空的魚缸會由 fish_animation 模組負責顯示提示
    html_render = st.session_state.tank.render_as_html()
    components.html(html_render, height=st.session_state.tank.height + 40, width=st.session_state.tank.width + 40)



# --- 5. 側邊欄 ---
st.sidebar.header("關於這個專案")
st.sidebar.info(
    "這是一個結合了手繪畫布、機器學習和動畫的 Streamlit 互動應用。\n\n"
    "**技術棧:**\n"
    "- **前端:** Streamlit, HTML/CSS\n"
    "- **繪圖:** streamlit-drawable-canvas\n"
    "- **AI 模型:** TensorFlow/Keras\n"
    "- **動畫/圖像:** Pillow"
)
st.sidebar.header("魚缸狀態")
st.sidebar.metric("目前魚缸中的魚數量", f"{len(st.session_state.tank.fishes)} 隻")
st.sidebar.image("https://storage.googleapis.com/kaggle-avatars/images/1332573-kg.png", width=150)