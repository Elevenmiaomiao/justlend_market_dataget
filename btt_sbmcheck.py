#  │＼＿＿╭╭╭╭╭＿＿／│ 
# │　　　　　　　　　　　│　　　 
# │　　　　　　　　　　　│　　　 
# │　●　　　　　　　●　│ 
# │≡　　╰┬┬┬╯　　≡│ 
# │　　　　╰—╯　　　　│　 
# ╰——┬Ｏ———Ｏ┬——╯ 
#     ╭—＾＿＿＾—╮
#      │〈=－﹏－=〉│ 
#   ╭═Ｏ════Ｏ═╮ 
#   │＊　　　＊　　＊│ 
#   │　　　＊　　　　│ 
#   │　＊　　　　＊　│ 
#   ╰════════╯
# 猫咪镇楼，代码才能畅行无阻
#　  ∧_∧　　　　∧_∧　 　　∧_∧　 　　　∧_∧　　　   
# 　（^ .^）　　（^ 、^）　 （^ 0^）　  （^ Д^）   
# ---∪-∪------∪-∪-------∪-∪-------∪-∪--- 


import requests
import csv
import time

# 定义抵押因子
COLLATERAL_FACTORS = {
    "TRX": 0.75,
    "USDD": 0.85,
    "USDT": 0.75,
    "wstUSDT": 0.75,
    "sTRX": 0.75,
    "SUN": 0.5,
    "BTT": 0.6,
    "NFT": 0.6,
    "JST": 0.6,
    "WIN": 0.5,
    "USDJ": 0.75,
    "TUSD": 0.75,
    "BTC": 0.75,
    "ETH": 0.75,
    "ETHB": 0.75,
    "WBTT": 0,
    "SUNOLD": 0,
    "USDCOLD": 0,
    "BUSDOLD": 0
}

# 定义 API key
API_KEY = "贴入你的tronscanAPI key"
HEADERS = {"TRON-PRO-API-KEY": API_KEY}

# 获取 jBTT 持有者信息（支持分页）
def get_jbtt_holders():
    url = "https://apilist.tronscanapi.com/api/token_trc20/holders"
    holders = []
    limit = 50
    offset = 0

    while True:
        params = {
            "contract_address": "TUaUHU9Dy8x5yNi1pKnFYqHWojot61Jfto",
            "limit": limit,
            "start": offset
        }
        response = requests.get(url, params=params, headers=HEADERS)
        response.raise_for_status()
        data = response.json().get("trc20_tokens", [])

        if not data:
            break

        holders.extend(data)
        offset += limit

        if len(data) < limit:
            break

    print(f"共找到 {len(holders)} 个 jBTT 持有者（也就是BTT存款者）。")
    if not holders:
        print("未找到持有者，一般不会出现这种问题，大概率是你的 APIkey 错了，或 tronscan 噶了。")
    return holders

# 获取账户在 JustLend 中的存款和借款信息（支持分页）
def get_justlend_data(address):
    url = f"https://apilist.tronscanapi.com/api/participate_project?justLendFilter=0&address={address}"
    projects = []
    offset = 0
    limit = 50

    while True:
        params = {"start": offset, "limit": limit}
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json().get("projects", [])

        if not data:
            break

        projects.extend(data)
        offset += limit

        if len(data) < limit:
            break

    justlend_data = []

    for project in projects:
        if project.get("project_name") == "JustLend DAO":
            justlend_data.extend(project.get("data", []))

    if not justlend_data:
        print(f"地址 {address} 未找到任何 JustLend 数据。")
    return justlend_data

# 计算允许借出资产的最大价值和已借出资产的价值
def calculate_values(data):
    max_borrow_value = 0
    borrowed_value = 0
    total_supply_value = 0
    btt_supply_value = 0
    btt_supply_balance = 0

    for item in data:
        currency_info = item.get("currency_info", {})
        token_abbr = currency_info.get("tokenAbbr")
        value_in_usd = item.get("value_in_usd", 0)
        balance = item.get("balance", 0)

        if item.get("type") == "Supply":
            total_supply_value += value_in_usd
            if token_abbr == "BTT":
                btt_supply_value += value_in_usd
                btt_supply_balance += balance

            collateral_factor = COLLATERAL_FACTORS.get(token_abbr, 0)
            max_borrow_value += value_in_usd * collateral_factor
        elif item.get("type") == "Borrow":
            borrowed_value += value_in_usd

    return max_borrow_value, borrowed_value, total_supply_value, btt_supply_value, btt_supply_balance

# 主函数
if __name__ == "__main__":
    holders = get_jbtt_holders()
    rows = []
    summary_rows = []

    for holder in holders:
        address = holder.get("holder_address")
        print(f"正在处理地址：{address}")
        justlend_data = get_justlend_data(address)
        
        max_borrow_value, borrowed_value, total_supply_value, btt_supply_value, btt_supply_balance = calculate_values(justlend_data)

        risk_value = borrowed_value / max_borrow_value if max_borrow_value > 0 else 0

        for item in justlend_data:
            currency_info = item.get("currency_info", {})
            token_abbr = currency_info.get("tokenAbbr")
            balance = item.get("balance", 0)
            value_in_usd = item.get("value_in_usd", 0)

            rows.append({
                "Address": address,
                "Type": item.get("type"),
                "Token": token_abbr,
                "Balance": balance,
                "Value (USD)": value_in_usd,
                "Max Borrow Value": max_borrow_value,
                "Borrowed Value": borrowed_value,
                "Risk Value": risk_value
            })

        summary_rows.append({
            "Address": address,
            "Total Supply Value": total_supply_value,
            "Max Borrow Value": max_borrow_value,
            "Borrowed Value": borrowed_value,
            "BTT Supply Value (USD)": btt_supply_value,
            "BTT Supply Balance": btt_supply_balance
        })

        time.sleep(0.2)  # 避免接口请求过于频繁

    # 检查是否有数据写入
    if rows:
        # 输出详细数据为 CSV 文件
        with open("justlend_report.csv", "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "Address", "Type", "Token", "Balance", "Value (USD)", 
                "Max Borrow Value", "Borrowed Value", "Risk Value"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(rows)

        print("详细数据已成功写入 justlend_report.csv 文件！")

    if summary_rows:
        # 输出汇总数据为 CSV 文件
        with open("justlend_summary.csv", "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "Address", "Total Supply Value", "Max Borrow Value", "Borrowed Value", 
                "BTT Supply Value (USD)", "BTT Supply Balance"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            writer.writerows(summary_rows)

        print("汇总数据已成功写入 justlend_summary.csv 文件！")
