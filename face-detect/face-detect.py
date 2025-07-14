# Скрипт позволяет получать события по детекции лиц от камеры TVT серии E4

import socket
import threading
import hashlib
import base64
import re
import os
from datetime import datetime

HOST = "192.168.226.222"
PORT = 18000
BUFFER_SIZE = 1024 * 64  # расширенный буфер

output_dir = "images"
os.makedirs(output_dir, exist_ok=True)
image_counter = 0

def extract_tag_cdata(xml: str, tag: str):
    """
    Извлекает содержимое <![CDATA[...]]> из заданного тега.
    """
    pattern = fr"<{tag}[^>]*><!\[CDATA\[(.*?)\]\]>"
    match = re.search(pattern, xml, re.DOTALL)
    return match.group(1).strip() if match else None

def extract_tag_plain(xml: str, tag: str):
    """
    Извлекает числовое значение или обычный текст без CDATA.
    """
    pattern = fr"<{tag}[^>]*>(.*?)</{tag}>"
    match = re.search(pattern, xml)
    return match.group(1).strip() if match else None

def save_base64_image(base64_data, mac, timestamp_ms):
    global image_counter
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_dir}/image_{image_counter}_{mac}_{timestamp}.jpg"
        image_counter += 1

        with open(filename, "wb") as f:
            f.write(base64.b64decode(base64_data))
        print(f"[✔] Сохранено: {filename}")
    except Exception as e:
        print(f"[!] Ошибка при сохранении: {e}")

def handle_client(conn, addr):
    print(f"{addr} подключился")
    try:
        data_buffer = b""
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            data_buffer += data

            # Простейшее завершение пакета по </config>
            if b"</config>" not in data_buffer:
                continue

            try:
                request = data_buffer.decode(errors="ignore")
            except Exception as e:
                continue

            base64_data = extract_tag_cdata(request, "sourceBase64Data")
            mac = extract_tag_cdata(request, "mac") or "UNKNOWN_MAC"
            time_val = extract_tag_plain(request, "currentTime") or "UNKNOWN_TIME"

            if base64_data:
                hash_value = hashlib.sha256(data_buffer).hexdigest()
                print(f"\n[TCP] {addr}")
                print(f"MAC: {mac}")
                print(f"Time: {time_val}")
                print(f"SHA256: {hash_value}")
                print(f"Base64 length: {len(base64_data)}")

                save_base64_image(base64_data, mac.replace(":", "_"), time_val)

            data_buffer = b""  # сброс на следующее сообщение

    except Exception as e:
        print(f"[!] Ошибка: {e}")
    finally:
        print(f"{addr} отключился")
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"MSG start TCP server successfully on {HOST}:{PORT}")

        while True:
            conn, addr = server.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

try:
    start_server()
except KeyboardInterrupt:
    print("\nMSG stop TCP server.")
