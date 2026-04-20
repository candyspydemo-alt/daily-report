import requests
import json
from datetime import datetime
import os

# 1. 設定 Header
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 2. 取得日期 (測試時可手動改成 "20260417")
today = datetime.now().strftime("%Y%m%d")
# today = "20260417" # 測試完記得註解掉這一行，恢復上面那行

# 💡 關鍵修正：改用 BFI82U API (三大法人買賣金額統計)
url = f"https://www.twse.com.tw/rwd/zh/fund/BFI82U?date={today}&response=json"

try:
    res = requests.get(url, headers=headers, timeout=15)
    data = res.json()
except Exception as e:
    print(f"❌ 請求失敗: {e}")
    exit(0)

# 3. 檢查是否有資料
if data.get("stat") != "OK" or "data" not in data:
    print(f"⚠️ {today} 查無金額統計資料，可能尚未收盤或假日。")
    exit(0)

# 4. 解析金額 (BFI82U 的資料格式固定)
# data["data"] 的順序通常是：0.自營商(避險), 1.自營商(自行買賣), 2.投信, 3.外資及陸資
# 我們需要抓的是「買賣差額」(索引第 3 欄)
try:
    # 這裡對應網頁上的各個法人
    dealer_self = float(data["data"][1][3].replace(",", "")) # 自營商(自行)
    dealer_hedge = float(data["data"][0][3].replace(",", "")) # 自營商(避險)
    investment = float(data["data"][2][3].replace(",", "")) # 投信
    foreign = float(data["data"][3][3].replace(",", ""))    # 外資

    dealer_total = dealer_self + dealer_hedge
    total_sum = dealer_total + investment + foreign

    result = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "foreign": round(foreign / 100000000, 2),
        "investment": round(investment / 100000000, 2),
        "dealer": round(dealer_total / 100000000, 2),
        "total": round(total_sum / 100000000, 2)
    }

    # 儲存 JSON
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 金額更新成功: {result}")

except (IndexError, ValueError) as e:
    print(f"❌ 解析資料出錯: {e}")
    exit(0)

# --- 5. LINE Messaging API 發送 ---
def send_line_push(res_data):
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    u_id = os.getenv("LINE_USER_ID")
    if not token or not u_id: return

    endpoint = "https://api.line.me/v2/bot/message/push"
    headers_line = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    
    msg = (
        f"📊 {res_data['date']} 三大法人買賣金額\n"
        f"-------------------\n"
        f"🏢 外資：{res_data['foreign']} 億\n"
        f"🏛️ 投信：{res_data['investment']} 億\n"
        f"⚖️ 自營：{res_data['dealer']} 億\n"
        f"-------------------\n"
        f"💰 合計：{res_data['total']} 億\n"
        f"🔗 網頁：https://candyspydemo-alt.github.io/daily-report/"
    )

    payload = {"to": u_id, "messages": [{"type": "text", "text": msg}]}
    requests.post(endpoint, headers=headers_line, json=payload)
    print("📱 LINE 通知已發送")

send_line_push(result)
