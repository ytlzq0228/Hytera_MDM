import sys
import os
import time
import re
import configparser
import aprs
import requests
import json
from typing import Optional
from datetime import datetime

CACHE_FILE = "dmr_cache.json"


SSID_ICON="Q"

APRS_Server="china.aprs2.net:14580"

# 加载缓存
def load_cache() -> dict:
	if os.path.exists(CACHE_FILE):
		try:
			with open(CACHE_FILE, "r", encoding="utf-8") as f:
				return json.load(f)
		except Exception as e:
			print(f"[!] 加载缓存失败: {e}")
	return {}

# 保存缓存
def save_cache(cache: dict):
	try:
		os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)  # 如果指定了目录，确保它存在
		with open(CACHE_FILE, "w", encoding="utf-8") as f:
			json.dump(cache, f, ensure_ascii=False, indent=2)
	except FileNotFoundError:
		# 没有路径时默认使用当前目录创建文件
		with open("dmr_cache.json", "w", encoding="utf-8") as f:
			json.dump(cache, f, ensure_ascii=False, indent=2)
	except Exception as e:
		print(f"[!] 保存缓存失败: {e}")


def get_CALLSIGN(dmr_id):
	cache = load_cache()
	if dmr_id in cache:
		print(f"来自缓存: {dmr_id}")
		return cache[dmr_id].get('callsign')
	url = f"https://radioid.net/api/dmr/user?id={dmr_id}"
	try:
		response = requests.get(url, timeout=10)
		response.raise_for_status()  # 如果状态码非 200，将抛出异常
		data = response.json()

		if not data or "results" not in data or not data["results"]:
			print(f"[!] No result found for DMR ID: {dmr_id}")
			return None

		user_info = data["results"][0]
		print("查询成功RadioID.net:")
		print(f"  DMR ID:	 {user_info.get('id')}")
		print(f"  呼号:	   {user_info.get('callsign')}")
		print(f"  姓名:	   {user_info.get('fname', '')} {user_info.get('lname', '')}")
		print(f"  国家:	   {user_info.get('country')}")
		print(f"  州/省:	  {user_info.get('state')}")
		print(f"  城市:	   {user_info.get('city')}")
		print(f"  备注:   {user_info.get('remarks')}")
		cache[dmr_id] = user_info
		save_cache(cache)
		return user_info.get('callsign')
	except requests.RequestException as e:
		print(f"[!] HTTP error: {e}")
	except ValueError as e:
		print(f"[!] JSON parse error: {e}")


def aprs_password(callsign: str) -> int:
    """
    根据 APRS callsign 计算 APRS-IS 验证用的 password。
    输入：
        callsign: 例如 "N0CALL"
    返回：
        password: 整数形式，如 12345
    """
    callsign = callsign.upper().split("-")[0]  # 去除 SSID 部分（如 N0CALL-1 → N0CALL）
    hash_val = 0x73e2  # 初始值

    for i, char in enumerate(callsign):
        if i % 2 == 0:
            hash_val ^= ord(char) << 8
        else:
            hash_val ^= ord(char)

    return hash_val & 0x7FFF  # 结果只保留 15 位（兼容传统实现）


def aprs_report(lat_input, lon_input, device_name, issiRadioId, device_id):
	device_ssid=""
	try:
		CALLSIGN=get_CALLSIGN(issiRadioId)
		APRS_PASSWORD=str(aprs_password(CALLSIGN))
		print(f"issiRadioId:{issiRadioId},CALLSIGN:{CALLSIGN},APRS_PASSWORD:{APRS_PASSWORD}")
		decimal_lat = float(lat_input)
		lat_dir = "N" if decimal_lat >= 0 else "S"
		lat_degrees = int(abs(decimal_lat))
		lat_minutes = (abs(decimal_lat) - lat_degrees) * 60
	
		# 经度转换
		decimal_lon = float(lon_input)
		lon_dir = "E" if decimal_lon >= 0 else "W"
		lon_degrees = int(abs(decimal_lon))
		lon_minutes = (abs(decimal_lon) - lon_degrees) * 60

		# 格式化为 APRS 格式
		lat = f"{lat_degrees:02d}{lat_minutes:05.2f}"
		lon = f"{lon_degrees:03d}{lon_minutes:05.2f}"

		device_ssid=f"{CALLSIGN}-H{device_id[-1]}"
		print(f"device_ssid:{device_ssid}")
		frame_text=(f'{device_ssid}>PYTHON,TCPIP*,qAC,{device_ssid}:!{lat}{lat_dir}/{lon}{lon_dir}{SSID_ICON}APRS by Hytera MDM from {device_name} report').encode()
		callsign = CALLSIGN.encode('utf-8')
		password = APRS_PASSWORD.encode('utf-8')
		
		# 定义 APRS 服务器地址和端口（字节形式）
		server_host = APRS_Server.encode('utf-8')  # 使用 rotate.aprs2.net 服务器和端口 14580
		
		# 创建 TCP 对象并传入服务器信息
		a = aprs.TCP(callsign, password, servers=[server_host])
		#a = aprs.TCP(callsign, password)
		a.start()
		aprs_return=a.send(frame_text)
		if aprs_return==len(frame_text)+2:
			print('APRS Report Good Length:%s'%aprs_return)
		else:
			print('APRS Report Return:%s Frame Length: %s Bad Request..'%(aprs_return,frame_text))
		
	except Exception as err:
		print(f"APRS Report Error: {err}")
	finally:
		return device_ssid

if __name__ == "__main__":
	#print(aprs_password("BI1FQO"))
	aprs_report("-23.56729", "-46.65940", "device_name", "4606666", "428")