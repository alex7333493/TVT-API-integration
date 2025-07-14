# Скрипт для подписки на события от терминала с распознаванием лиц.
# При получении данных, они отображаются в терминале

import http.client
import base64
import xml.etree.ElementTree as ET
import datetime

host = "192.168.226.201"
port = 8080

xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<config version="1.7" xmlns="http://www.ipc.com/ver10">
  <types>
    <openAlramObj>
      <enum>MOTION</enum>
    </openAlramObj>
    <subscribeRelation>
      <enum>ALARM</enum>
    </subscribeRelation>
    <subscribeTypes>
      <enum>BASE_SUBSCRIBE</enum>
    </subscribeTypes>
  </types>
  <channelID type="uint32">0</channelID>
  <initTermTime type="uint32">0</initTermTime>
  <subscribeFlag type="subscribeTypes">BASE_SUBSCRIBE</subscribeFlag>
  <subscribeList type="list" count="1">
    <item>
      <smartType type="openAlramObj">VFD_MATCH</smartType>
      <subscribeRelation type="subscribeRelation">ALARM_FEATURE</subscribeRelation>
    </item>
  </subscribeList>
</config>
"""

auth = base64.b64encode(b"admin:P@rol123").decode()

conn = http.client.HTTPConnection(host, port, timeout=300)
headers = {
    "Authorization": f"Basic {auth}",
    "Content-Type": "application/xml",
    "Content-Length": str(len(xml_data)),
    "Connection": "keep-alive",
    "Keep-Alive": "300"
}

print("[INFO] Отправляю подписку...")
conn.request("POST", "/SetSubscribe", body=xml_data, headers=headers)
response = conn.getresponse()
print("[INFO] Ответ камеры:", response.status)
print(response.read().decode())

print("[INFO] Готов к приёму событий! Нажмите Ctrl+C для выхода.")

def format_time(ts: str) -> str:
    try:
        ts_int = int(ts)
        dt = datetime.datetime.fromtimestamp(ts_int / 1_000_000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"

try:
    while True:
        # Ожидаем Content-Length
        data = b""
        while b"Content-Length" not in data:
            chunk = conn.sock.recv(4096)
            if not chunk:
                continue
            data += chunk
        try:
            headers_part = data.decode(errors="ignore")
            headers_lines = headers_part.split("\r\n")
            content_length = None
            for line in headers_lines:
                if "Content-Length" in line:
                    content_length = int(line.split(":")[1].strip())
                    break
            if not content_length:
                print("[ERROR] Content-Length не найден")
                continue
        except Exception as e:
            print("[ERROR] Не удалось получить Content-Length:", str(e))
            continue

        # Ждём тело
        body_start = data.find(b"\r\n\r\n")
        if body_start == -1:
            continue
        body = data[body_start+4:]
        while len(body) < content_length:
            chunk = conn.sock.recv(4096)
            if not chunk:
                break
            body += chunk

        print(f"[INFO] Получен XML: {len(body)} байт")
        with open("last_raw_event.xml", "wb") as f:
            f.write(body)

        try:
            root = ET.fromstring(body.decode(errors="ignore"))
            ns = {'ns': 'http://www.ipc.com/ver10'}
            name = root.find('.//ns:name', ns)
            idnum = root.find('.//ns:identifyNum', ns)
            ctime = root.find('.//ns:currentTime', ns)

            print(f"Имя: {name.text if name is not None else 'N/A'}")
            print(f"ID Num: {idnum.text if idnum is not None else 'N/A'}")
            print(f"currentTime: {format_time(ctime.text) if ctime is not None else 'N/A'}")

        except ET.ParseError as e:
            print(f"[ERROR] Некорректный XML: {str(e)}")

except KeyboardInterrupt:
    print("\n[INFO] Остановлено пользователем. Пока! 👋")
    conn.close()
