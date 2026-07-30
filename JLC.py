# -*- coding: UTF-8 -*-
import subprocess, sys, os, importlib

# ======================【自动安装缺失依赖】======================
_REQUIRED = {
    'requests': 'requests',
}

for _mod, _pkg in _REQUIRED.items():
    try:
        importlib.import_module(_mod)
    except ImportError:
        print(f"[自动安装] 正在安装 {_pkg} ...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', _pkg, '-q'])
        print(f"[自动安装] {_pkg} 安装完成")
# =================================================================

import json
import time
import random
import requests
from requests.exceptions import RequestException

# ======================【从 GitHub Actions 环境变量获取 Token】======================
TOKEN_LIST = os.environ.get('TOKEN_LIST', '')   # 优先读取环境变量，若未设置则为空字符串
# ==================================================================================

# -------- 嘉立创商城接口（原有签到不变） --------
SIGN_URL = 'https://m.jlc.com/api/activity/sign/signIn?source=3'
ASSET_URL = "https://m.jlc.com/api/appPlatform/center/assets/selectPersonalAssetsInfo"
SEVEN_DAY_BONUS_URL = "https://m.jlc.com/api/activity/sign/receiveVoucher"

# -------- 立创开源平台 oshwhub【最终正确签到接口：api/users/signIn】 --------
OSH_BASE = "https://oshwhub.com"
OSH_SIGN_URL = f"{OSH_BASE}/api/users/signIn"  # 用户提供有效接口
OSH_POINT_URL = f"{OSH_BASE}/api/user/getUserPoint"

# APP固定UA（商城+开源通用）
HEADERS_BASE = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/20) JlcMobileApp',
    'Content-Type': 'application/json'
}


def mask_account(account):
    """账号脱敏打印"""
    if len(account) >= 4:
        return account[:2] + '****' + account[-2:]
    return '****'


def jlc_shop_sign(access_token):
    """嘉立创商城签到（金豆），原有逻辑不变"""
    headers = HEADERS_BASE.copy()
    headers['X-JLC-AccessToken'] = access_token
    mask_tk = mask_account(access_token)
    try:
        # 查询资产
        bean_resp = requests.get(ASSET_URL, headers=headers, timeout=12)
        bean_resp.raise_for_status()
        bean_json = bean_resp.json()
        cust_code = bean_json['data']['customerCode']
        now_gold = bean_json['data']['integralVoucher']
        cust_mask = mask_account(cust_code)

        # 商城签到
        sign_resp = requests.get(SIGN_URL, headers=headers, timeout=12)
        sign_resp.raise_for_status()
        sign_json = sign_resp.json()

        if not sign_json.get("success"):
            msg = sign_json.get("message", "商城签到异常")
            if "已经签到" in msg:
                print(f"ℹ️【商城-{cust_mask}】今日已签到")
                return
            print(f"❌【商城-{cust_mask}】签到失败：{msg}")
            return

        sign_data = sign_json.get("data", {})
        gain = sign_data.get("gainNum", 0)
        status = sign_data.get("status", 0)
        if status <= 0:
            print(f"ℹ️【商城-{cust_mask}】无签到奖励")
            return

        if gain and int(gain) > 0:
            total = now_gold + gain
            print(f"✅【商城-{cust_mask}】签到成功，获得{gain}金豆，现有{total}")
        else:
            # 第七天额外领奖
            seven_resp = requests.get(SEVEN_DAY_BONUS_URL, headers=headers, timeout=12)
            seven_json = seven_resp.json()
            bonus = seven_json.get("data", {}).get("gainNum",8)
            if seven_json.get("success"):
                total = now_gold + bonus
                print(f"🎉【商城-{cust_mask}】满7天领奖，获{bonus}金豆，现有{total}")
            else:
                print(f"ℹ️【商城-{cust_mask}】第七天领奖失败")

    except RequestException as e:
        print(f"❌【商城-{mask_tk}】网络异常：{str(e)}")
    except KeyError as e:
        print(f"❌【商城-{mask_tk}】字段缺失：{str(e)}")
    except Exception as e:
        print(f"❌【商城-{mask_tk}】未知错误：{str(e)}")


def main():
    token_arr = [tk.strip() for tk in TOKEN_LIST.split(",") if tk.strip()]
    if not token_arr:
        print("❌ 请在 GitHub Actions 的环境变量中设置 TOKEN_LIST！")  # 修改提示信息
        return
    print(f"🏁 总计{len(token_arr)}个账号，开始商城平台签到")

    for idx, token in enumerate(token_arr):
        print(f"\n===== 正在处理第{idx+1}/{len(token_arr)}个账号 {mask_account(token)} =====")
        jlc_shop_sign(token)
        # 非最后一个账号随机休眠5~15秒防风控
        if idx != len(token_arr)-1:
            sleep_sec = random.randint(120,240)
            print(f"⏳ 休眠{sleep_sec}s后处理下一号")
            time.sleep(sleep_sec)

    print("\n🏁 全部账号签到任务执行完毕！")


if __name__ == '__main__':
    print("开始执行签到任务")
    sleep_sec = random.randint(120,240)
    print(f"计划等待{sleep_sec}s后执行第一个账号的签到任务")
    time.sleep(sleep_sec)
    main()