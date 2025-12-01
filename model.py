# AI 模型 (model.py)
import numpy as np
import os
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from sklearn.model_selection import train_test_split

# 匯入我們自己的 utils 函式
from app_utils import load_quickdraw_images

# --- 1. 模型架構定義 ---
def create_cnn_model(input_shape=(28, 28, 1)):
    """
    建立一個用於二分類的 CNN 模型。

    Args:
        input_shape (tuple): 輸入圖片的形狀。

    Returns:
        tf.keras.Model: 一個未經編譯的 Keras 模型。
    """
    model = Sequential([
        # 層 1: 卷積層 + 池化層
        Conv2D(32, (3, 3), activation='relu', input_shape=input_shape),
        MaxPooling2D((2, 2)),
        
        # 層 2: 卷積層 + 池化層
        Conv2D(64, (3, 3), activation='relu'),
        MaxPooling2D((2, 2)),
        
        # 層 3: 扁平化層
        Flatten(),
        
        # 層 4: 全連接層
        Dense(128, activation='relu'),
        Dropout(0.5), # 加入 Dropout 防止過擬合
        
        # 輸出層: 二分類，使用 sigmoid 激活函數
        Dense(1, activation='sigmoid')
    ])
    
    return model

# --- 2. 訓練與儲存模型 ---
def train_and_save_model(model_path="fish_classifier.h5"):
    """
    載入資料、建立、編譯、訓練並儲存模型。
    """
    print("--- 開始模型訓練流程 ---")
    
    # 載入正樣本 (魚) 和負樣本 (貓)
    # 我們使用貓的資料集作為 "非魚" 的代表
    fish_images = load_quickdraw_images("fish", max_items=10000)
    cat_images = load_quickdraw_images("cat", max_items=10000)
    
    if fish_images.size == 0 or cat_images.size == 0:
        print("錯誤：無法載入訓練資料，請檢查 utils.py 或網路連線。")
        return

    # 建立標籤：1 代表 '魚', 0 代表 '非魚' (貓)
    fish_labels = np.ones(fish_images.shape[0])
    cat_labels = np.zeros(cat_images.shape[0])
    
    # 合併資料與標籤
    X = np.concatenate((fish_images, cat_images), axis=0)
    y = np.concatenate((fish_labels, cat_labels), axis=0)
    
    #正規化像素值到 0-1 之間
    X = X.astype('float32') / 255.0
    
    # 增加一個 "channel" 維度，以符合 CNN 輸入 (N, 28, 28) -> (N, 28, 28, 1)
    X = np.expand_dims(X, axis=-1)
    
    # 切分訓練集和驗證集
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"訓練資料形狀: {X_train.shape}")
    print(f"驗證資料形狀: {X_val.shape}")
    
    # 建立模型
    model = create_cnn_model(input_shape=X_train.shape[1:])
    
    # 編譯模型
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy', # 二分類使用二元交叉熵
        metrics=['accuracy']
    )
    
    print("\n--- 模型摘要 ---")
    model.summary()
    
    # 訓練模型
    print("\n--- 開始訓練 ---")
    history = model.fit(
        X_train, y_train,
        epochs=10, # 為了快速展示，只訓練10個週期
        batch_size=128,
        validation_data=(X_val, y_val)
    )
    
    # 儲存模型
    print(f"\n--- 訓練完成，儲存模型至 {model_path} ---")
    model.save(model_path)
    print("模型儲存成功！")

# --- 3. 載入與預測 ---
def load_ai_model(model_path="fish_classifier.h5"):
    """
    載入預先訓練好的 Keras 模型。
    
    Args:
        model_path (str): 模型的檔案路徑。
        
    Returns:
        model: 載入完成的模型物件，若失敗則回傳 None。
    """
    if not os.path.exists(model_path):
        print(f"錯誤：模型檔案 '{model_path}' 不存在。")
        print("請先執行 'python model.py' 來訓練並產生模型檔案。")
        return None
    
    try:
        model = load_model(model_path)
        print(f"模型 '{model_path}' 載入成功！")
        return model
    except Exception as e:
        print(f"模型載入失敗: {e}")
        return None

def predict_image(image_array, model):
    """
    使用載入的模型來預測圖片是否為魚。
    
    Args:
        image_array (np.array): 經過前處理的圖片陣列 (28x28, 黑底白線)。
        model: 預訓練 Keras 模型物件。
        
    Returns:
        tuple: (is_fish, confidence)
    """
    if model is None:
        # 如果模型未載入，回傳預設值
        return False, 0.0

    #正規化並調整形狀以符合模型輸入
    img_processed = image_array.astype('float32') / 255.0
    img_processed = np.expand_dims(img_processed, axis=(0, -1)) # (1, 28, 28, 1)
    
    # 進行預測
    prediction = model.predict(img_processed)[0][0]
    
    confidence = float(prediction)
    is_fish = confidence > 0.5 # 假設閾值為 0.5
    
    return is_fish, confidence

# --- 測試用 ---
if __name__ == '__main__':
    # 執行此腳本將會觸發完整的訓練流程
    train_and_save_model()
