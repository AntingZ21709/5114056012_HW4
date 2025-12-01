# 魚缸動畫 (fish_animation.py)
import random
import base64
from io import BytesIO
from PIL import Image
import json

def pil_to_base64(image: Image.Image) -> str:
    """將 Pillow 圖片物件轉換為 Base64 編碼的字串。"""
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

class Fish:
    """
    代表一隻魚的類別，現在使用傳入的 sprite 圖片。
    這個類別現在主要用於儲存魚的初始狀態，動畫邏輯已移至客戶端 JavaScript。
    """
    def __init__(self, bounds, sprite_image):
        """
        初始化一隻魚。

        Args:
            bounds (tuple): 魚缸的邊界 (width, height)。
            sprite_image (PIL.Image): 這隻魚的圖片 (需為 RGBA 格式以支援透明度)。
        """
        self.bounds = bounds
        
        # 儲存原始及水平翻轉的圖片
        self.sprite_right = sprite_image
        self.sprite_left = self.sprite_right.transpose(Image.FLIP_LEFT_RIGHT)
        
        self.width, self.height = self.sprite_right.size
        
        # 初始位置
        self.pos = [
            random.uniform(self.width, bounds[0] - self.width),
            random.uniform(self.height, bounds[1] - self.height)
        ]
        
        # 初始速度
        self.vel = [
            random.uniform(-2, 2),
            random.uniform(-1, 1)
        ]
        # 確保初始速度不為零
        if self.vel[0] == 0 and self.vel[1] == 0:
            self.vel[0] = 1

class FishTank:
    """
    管理整個魚缸的狀態與繪圖。
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.fishes = []
        self.background_image_url = "https://www.stickpng.com/assets/images/580b585b2edb1692510b5865.png"

    def add_fish(self, sprite_image):
        """
        新增一隻使用自訂 sprite 的魚到魚缸裡。
        
        Args:
            sprite_image (PIL.Image): 要新增的魚的圖片。
        """
        new_fish = Fish(bounds=(self.width, self.height), sprite_image=sprite_image)
        self.fishes.append(new_fish)
        print(f"新增一隻自訂魚！目前共有 {len(self.fishes)} 隻。")

    def render_as_html(self) -> str:
        """
        將魚缸狀態轉換為 HTML 和客戶端 JavaScript 以進行流暢的動畫渲染。
        """
        # 1. 準備魚的數據
        fishes_data = []
        for i, fish in enumerate(self.fishes):
            fishes_data.append({
                "id": f"fish-{i}",
                "pos": fish.pos,
                "vel": fish.vel,
                "width": fish.width,
                "height": fish.height,
                "sprite_left": f"data:image/png;base64,{pil_to_base64(fish.sprite_left)}",
                "sprite_right": f"data:image/png;base64,{pil_to_base64(fish.sprite_right)}",
            })

        # 2. 建立魚缸容器和魚的 <img> 元素
        tank_html = f"""
        <div id="fish-tank" style="
            width: {self.width}px;
            height: {self.height}px;
            background-color: #E0F7FA;
            background-image: url('{self.background_image_url}');
            background-size: contain;
            background-position: center;
            background-repeat: no-repeat;
            position: relative;
            overflow: hidden;
            margin: auto;
            border: 2px solid #888;
        ">
        """

        if not self.fishes:
            tank_html += """
            <div style="
                position: absolute; top: 50%; left: 50%;
                transform: translate(-50%, -50%); color: #666;
                font-size: 1.2em; text-align: center; font-weight: bold;
            ">
                魚缸是空的，<br>快畫一隻魚吧！
            </div>
            """
        else:
            for fish_data in fishes_data:
                tank_html += f"""
                <img id="{fish_data['id']}" src="{fish_data['sprite_right']}" style="
                    position: absolute;
                    left: 0; top: 0; /* JS will control position via transform */
                    width: {fish_data['width']}px;
                    height: {fish_data['height']}px;
                    transform: translate({fish_data['pos'][0]}px, {fish_data['pos'][1]}px);
                    will-change: transform;
                ">
                """
        
        tank_html += "</div>"

        # 3. 建立客戶端 JavaScript 動畫腳本
        js_script = f"""
        <script>
        // 確保腳本只執行一次
        if (!window.fishAnimationStarted) {{
            window.fishAnimationStarted = true;

            const tank = document.getElementById('fish-tank');
            const fishes = {json.dumps(fishes_data)};
            const bounds = {{ width: {self.width}, height: {self.height} }};

            function updateFish(fish) {{
                // 更新位置
                fish.pos[0] += fish.vel[0];
                fish.pos[1] += fish.vel[1];

                // 隨機微調速度
                if (Math.random() < 0.02) {{
                    fish.vel[0] += Math.random() * 0.6 - 0.3;
                    fish.vel[1] += Math.random() * 0.6 - 0.3;
                }}

                // 邊界碰撞檢測
                if (fish.pos[0] < 0) {{
                    fish.pos[0] = 0;
                    fish.vel[0] *= -1;
                }} else if (fish.pos[0] > bounds.width - fish.width) {{
                    fish.pos[0] = bounds.width - fish.width;
                    fish.vel[0] *= -1;
                }}

                if (fish.pos[1] < 0) {{
                    fish.pos[1] = 0;
                    fish.vel[1] *= -1;
                }} else if (fish.pos[1] > bounds.height - fish.height) {{
                    fish.pos[1] = bounds.height - fish.height;
                    fish.vel[1] *= -1;
                }}

                // 速度限制
                const speed = Math.sqrt(fish.vel[0]**2 + fish.vel[1]**2);
                if (speed > 4) {{
                    fish.vel[0] = (fish.vel[0] / speed) * 4;
                    fish.vel[1] = (fish.vel[1] / speed) * 4;
                }} else if (speed < 1.5) {{
                    fish.vel[0] = (fish.vel[0] / speed) * 1.5;
                    fish.vel[1] = (fish.vel[1] / speed) * 1.5;
                }}
            }}

            function animate() {{
                fishes.forEach(fish => {{
                    updateFish(fish);
                    
                    const fishElement = document.getElementById(fish.id);
                    if (fishElement) {{
                        // 更新 DOM
                        fishElement.style.transform = `translate(${'{'}fish.pos[0]{'}'}px, ${'{'}fish.pos[1]{'}'}px)`;
                        
                        // 根據速度方向更新圖片
                        if (fish.vel[0] < 0) {{
                            if (fishElement.src !== fish.sprite_left) {{
                                fishElement.src = fish.sprite_left;
                            }}
                        }} else {{
                            if (fishElement.src !== fish.sprite_right) {{
                                fishElement.src = fish.sprite_right;
                            }}
                        }}
                    }}
                }});
                
                // 請求下一幀
                requestAnimationFrame(animate);
            }}

            // 只有當魚缸裡有魚時才啟動動畫
            if (fishes.length > 0) {{
                animate();
            }}
        }}
        </script>
        """

        return tank_html + js_script