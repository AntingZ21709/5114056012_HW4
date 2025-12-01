# 共用輔助函式 (utils.py)
import numpy as np
from PIL import Image
import os
import urllib.request
import cv2

def preprocess_image(canvas_image_data):
    """
    將 Streamlit Drawable Canvas 的輸出轉換為模型可用的格式。

    Args:
        canvas_image_data (np.array): 來自 st_canvas 的 RGBA 圖片資料。

    Returns:
        np.array: 處理過的圖片陣列。
    """
    # TODO: 根據你的模型輸入要求，完善這個函式。
    # 例如：灰階、尺寸調整、正規化等。

    if canvas_image_data is not None:
        # 轉換為 PIL Image 物件
        img = Image.fromarray(canvas_image_data.astype('uint8'), 'RGBA')
        
        # 轉換為灰階
        img_gray = img.convert('L')
        
        # 調整尺寸到 28x28 (配合 QuickDraw 資料集)
        img_resized = img_gray.resize((28, 28), Image.LANCZOS)
        
        # 轉換為 numpy array
        img_array = np.array(img_resized)
        
        # QuickDraw 是黑底白線，但畫布是白底黑線，所以需要反轉顏色
        img_inverted = 255 - img_array
        
        #正規化到 0-1 之間 (如果模型需要)
        # img_normalized = img_inverted / 255.0
        
        # 增加一個維度以符合模型輸入 (e.g., (1, 28, 28, 1))
        # return np.expand_dims(img_normalized, axis=(0, -1))
        
        return img_inverted
    
    return None

def download_quickdraw_dataset(dataset_name="fish", dest_path="."):
    """
    從 Google Cloud Storage 下載 QuickDraw 資料集的 .npy 檔案。

    Args:
        dataset_name (str): 要下載的資料集名稱 (例如 "fish", "cat", "apple")。
        dest_path (str): 儲存檔案的目標資料夾。

    Returns:
        str: 下載檔案的完整路徑，如果失敗則回傳 None。
    """
    file_name = f"{dataset_name}.npy"
    file_path = os.path.join(dest_path, file_name)
    
    # 檢查檔案是否已存在
    if os.path.exists(file_path):
        print(f"資料集 '{file_name}' 已存在於 '{file_path}'。")
        return file_path

    # 下載 URL
    url = f"https://storage.googleapis.com/quickdraw_dataset/full/numpy_bitmap/{file_name}"
    
    print(f"正在從 {url} 下載 '{file_name}'...")
    
    try:
        # 使用 urllib 進行下載
        urllib.request.urlretrieve(url, file_path)
        print(f"下載完成！檔案儲存於: {file_path}")
        return file_path
    except Exception as e:
        print(f"下載失敗: {e}")
        # 如果下載失敗，清理不完整的檔案
        if os.path.exists(file_path):
            os.remove(file_path)
        return None

def load_quickdraw_images(dataset_name="fish", max_items=5000):
    """
    下載並載入 QuickDraw 資料集，將其轉換為 28x28 的圖片陣列。

    Args:
        dataset_name (str): 要載入的資料集名稱。
        max_items (int): 要載入的最大圖片數量。

    Returns:
        np.array: 包含圖片資料的 NumPy 陣列，形狀為 (數量, 28, 28)。
                  圖片為黑底白線 (0-255)。
    """
    # 確保資料集已下載
    file_path = download_quickdraw_dataset(dataset_name)
    
    if file_path is None:
        return np.array([]) # 回傳空陣列

    # 載入 .npy 檔案
    # allow_pickle=True 是載入 QuickDraw 資料集所必需的
    images = np.load(file_path, encoding='latin1', allow_pickle=True)
    
    # 取前 max_items 筆資料
    images = images[:max_items]
    
    # 資料的數值範圍是 0-255，型別是 uint8
    # 將 784 的向量轉換為 28x28 的圖片
    images = images.reshape(-1, 28, 28)
    
    print(f"成功載入 {len(images)} 張 '{dataset_name}' 圖片，形狀為: {images.shape}")
    
    # QuickDraw .npy 檔案本身就是黑底白線，不需反轉
    return images

# --- 測試用 ---
if __name__ == '__main__':
    print("--- 測試 QuickDraw 資料集載入功能 ---")
    
    # 載入魚的圖片
    fish_images = load_quickdraw_images("fish", max_items=10)
    
    if fish_images.size > 0:
        # 使用 OpenCV 顯示第一張圖片以供驗證
        first_fish_image = fish_images[0]
        
        # 放大圖片以便查看
        display_image = cv2.resize(first_fish_image, (280, 280), interpolation=cv2.INTER_NEAREST)
        
        print("\n顯示第一張魚的圖片 (放大10倍)。")
        print("按任意鍵關閉視窗。")
        
        cv2.imshow('Sample Fish Image (28x28)', display_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("無法載入圖片進行測試。")
