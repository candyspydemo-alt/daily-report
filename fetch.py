import requests
import json
from datetime import datetime
import os

# 1. 設定 Header 模擬瀏覽器，防止被證交所阻擋
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 取得今日日期
today = datetime.now().strftime("%Y%m%d")
url = f"https://www.twse.com.tw/rwd/zh/fund/T86?date={today}&selectType=ALL&response=json"

try:
    res = requests.get(url, headers=headers, timeout=15)
    data = res.json()
except Exception as e:
    print(f"❌ 請求失敗: {e}")
    exit(0)

# 3. 檢查是否有資料（假日或尚未收盤會查無資料）
if data.get("stat") != "OK" or "data" not in data:
    print(f"⚠️ {today} 查無資料（可能尚未收盤、假日或 API 限制中）")
    exit(0)

foreign_total = 0
investment_total = 0
dealer_total = 0

# 4. 遍歷每檔股票，加總各法人的買賣超張數
for item in data["data"]:
    try:
        # T86 API 欄位索引: 
        # [2]: 外資, [10]: 投信, [11]: 自營商(合計)
        foreign_total += int(item[2].replace(",", ""))
        investment_total += int(item[10].replace(",", ""))
        dealer_total += int(item[11].replace(",", ""))
    except (ValueError, IndexError):
        continue

# 5. 計算總計
total_sum = foreign_total + investment_total + dealer_total

# 6. 整理結果 (將單位轉換為「億股」，四捨五入至小數點後兩位)
result = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "foreign": round(foreign_total / 100000000, 2),
    "investment": round(investment_total / 100000000, 2),
    "dealer": round(dealer_total / 100000000, 2),
    "total": round(total_sum / 100000000, 2)
}

# 7. 儲存為 JSON 檔案
try:
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 處理完成，已更新 data.json: {result}")
except Exception as e:
    print(f"❌ 檔案寫入失敗: {e}")

# --- 8. 新增：LINE Messaging API 發送功能 ---
def send_line_push(result_data):
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_USER_ID")
    
    if not token or not user_id:
        print("⚠️ 缺少 LINE 配置，跳過發送通知")
        return

    endpoint = "https://api.line.me/v2/bot/message/push"
    headers_line = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    # 設定通知訊息文字
    # 💡 這裡可以隨意調整你想要的排版
    message_text = (
        f"📊 {result_data['date']} 三大法人籌碼日報\n"
        f"-------------------\n"
        f"🏢 外資：{result_data['foreign']} 億\n"
        f"🏛️ 投信：{result_data['investment']} 億\n"
        f"⚖️ 自營：{result_data['dealer']} 億\n"
        f"-------------------\n"
        f"💰 合計：{result_data['total']} 億\n"
        f"🔗 網頁：https://candyspydemo-alt.github.io/daily-report/"
    )

    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
    }
    
    try:
        response = requests.post(endpoint, headers=headers_line, json=payload)
        if response.status_code == 200:
            print("📱 LINE 通知發送成功！")
        else:
            print(f"❌ LINE 通知發送失敗，錯誤碼: {response.status_code}, 內容: {response.text}")
    except Exception as e:
        print(f"❌ LINE 發送過程中發生錯誤: {e}")

# 執行發送
send_line_push(result)

print("done")
