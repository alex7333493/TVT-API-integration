# Скрипт платной парковки на камерах с распознаванием номеров. 
# Скрипт позволяет считать стоимость парковки.
# Для помощи в интеграции пишите на почту 7333493a@gmail.com


import socket, threading, base64, re, os, time, sqlite3, csv, sys, tempfile
from datetime import datetime, timedelta
from requests.auth import HTTPBasicAuth
import requests
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import win32api

# --- Настройки ---
HOST, PORT = "0.0.0.0", 18000
ENTRY_IP, EXIT_IP = "192.168.1.201", "192.168.1.202"
USER, PASS = "admin", "123456"
SAVE_DIR = "plates"
DB_FILE = "parking.db"

os.makedirs(f"{SAVE_DIR}/entry", exist_ok=True)
os.makedirs(f"{SAVE_DIR}/exit", exist_ok=True)

# --- База данных ---
db = sqlite3.connect(DB_FILE, check_same_thread=False)
cur = db.cursor()
cur.execute('''CREATE TABLE IF NOT EXISTS visits (
    id INTEGER PRIMARY KEY,
    plate TEXT,
    time_in INTEGER,
    time_out INTEGER,
    photo_in TEXT,
    photo_out TEXT,
    duration INTEGER,
    cost INTEGER
)''')
cur.execute('''CREATE TABLE IF NOT EXISTS whitelist (
    plate TEXT PRIMARY KEY
)''')
db.commit()

# --- Парсинг XML ---
def extract_tag(xml, tag):
    m = re.search(fr"<{tag}[^>]*><!\[CDATA\[(.*?)\]\]>", xml)
    return m.group(1).strip() if m else None

def extract_all_items(xml):
    return re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)

def extract_base64(block):
    m = re.search(r"<targetBase64Data[^>]*><!\[CDATA\[(.*?)\]\]>", block, re.DOTALL)
    return m.group(1).replace("\n", "").strip() if m else None

def extract_plate(block):
    return extract_tag(block, "plateNumber")

def convert_ts_fixed(raw):
    try:
        ts = int(str(raw).strip())
        if ts > 1e14:
            ts //= 1_000_000
        elif ts > 1e10:
            ts //= 1000
        if ts < 1000000000:
            raise ValueError("Bad timestamp")
        ts += 5 * 3600
    except Exception:
        ts = int(time.time())
    return ts

def fmt_time(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

def save_img(b64, plate, folder, ts):
    path = f"{SAVE_DIR}/{folder}/{plate}_{ts}.jpg"
    try:
        with open(path, "wb") as f:
            f.write(base64.b64decode(b64))
        return path
    except:
        return ""

def open_gate(ip):
    url = f"http://{ip}/ManualAlarmOut"
    headers = {'Content-Type': 'application/xml'}
    xml_on = '''<?xml version="1.0" encoding="UTF-8"?><config version="2.0.0" xmlns="http://www.ipc.com/ver10"><action><status>true</status></action></config>'''
    xml_off = xml_on.replace("true", "false")
    try:
        requests.post(url, data=xml_on, headers=headers, auth=HTTPBasicAuth(USER, PASS), timeout=2)
        time.sleep(2)
        requests.post(url, data=xml_off, headers=headers, auth=HTTPBasicAuth(USER, PASS), timeout=2)
    except Exception as e:
        print("Ошибка открытия шлагбаума:", e)

def calc_cost(sec, free_min, price_hour):
    if sec // 60 <= free_min:
        return 0
    return price_hour

def print_receipt(plate, t_in, t_out, duration, cost):
    content = f"ЧЕК\nНомер: {plate}\nВъезд: {fmt_time(t_in)}\nВыезд: {fmt_time(t_out)}\nДлительность: {duration//60} мин\nСумма: {cost} сум"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        win32api.ShellExecute(0, "print", tmp_path, None, ".", 0)
        print("🖨 Чек отправлен на печать")
    except Exception as e:
        print("Ошибка печати:", e)

# --- GUI ---
root = tk.Tk()
root.title("Платная парковка")
root.geometry("1200x800")

frame_top = tk.Frame(root)
frame_top.pack(side="top", fill="x")

# Левая колонка
f_left = tk.Frame(frame_top, width=400,height=520)
f_left.pack(side="left", fill="y", padx=5, pady=5)
f_left.pack_propagate(False)

tk.Label(f_left, text="ВЪЕЗД", font=("Arial", 14)).pack()
canvas_in = tk.Canvas(f_left, width=320, height=180)
canvas_in.pack()
lbl_in = tk.Label(f_left, text="Номер / Время", font=("Arial", 10))
lbl_in.pack()
btn_entry = tk.Button(f_left, text="Открыть въезд", command=lambda: open_gate(ENTRY_IP), font=("Arial", 12), height=2, width=25)
btn_entry.pack(pady=10)

tk.Label(f_left, text="Настройки", font=("Arial", 14)).pack(pady=5)
tk.Label(f_left, text="Бесплатно (мин):").pack()
entry_free = tk.Entry(f_left); entry_free.insert(0, "5"); entry_free.pack()
tk.Label(f_left, text="Цена за парковку (сум):").pack()
entry_price = tk.Entry(f_left); entry_price.insert(0, "15000"); entry_price.pack()

tk.Label(f_left, text="Белый список", font=("Arial", 14)).pack(pady=5)
entry_whitelist = tk.Entry(f_left)
entry_whitelist.pack()
def add_whitelist():
    plate = entry_whitelist.get().strip().upper()
    if plate:
        db.execute("INSERT OR IGNORE INTO whitelist (plate) VALUES (?)", (plate,))
        db.commit()
tk.Button(f_left, text="Добавить номер", command=add_whitelist).pack(pady=5)

# Средняя колонка
f_mid = tk.Frame(frame_top, width=400)
f_mid.pack(side="left", fill="y", padx=5, pady=5)
f_mid.pack_propagate(False)

tk.Label(f_mid, text="ВЫЕЗД", font=("Arial", 14)).pack()
canvas_in_mid = tk.Canvas(f_mid, width=320, height=180)
canvas_out_mid = tk.Canvas(f_mid, width=320, height=180)
canvas_in_mid.pack()
canvas_out_mid.pack()

# Правая колонка
f_right = tk.Frame(frame_top, width=400)
f_right.pack(side="left", fill="y", padx=5, pady=5)
f_right.pack_propagate(False)

lbl_out = tk.Label(f_right, text="Инфо", font=("Arial", 14), fg="blue", justify="left")
lbl_out.pack(pady=10)

btn_print = tk.Button(f_right, text="Печать чека", font=("Arial", 12), height=2, width=25)
btn_print.pack(pady=5)

btn_exit = tk.Button(f_right, text="Открыть выезд", command=lambda: open_gate(EXIT_IP), font=("Arial", 12), height=2, width=25)
btn_exit.pack(pady=5)

tk.Label(f_right, text="Отчет", font=("Arial", 14)).pack(pady=5)
tk.Label(f_right, text="С даты (YYYY-MM-DD):").pack()
entry_from = tk.Entry(f_right); entry_from.insert(0, datetime.now().strftime("%Y-%m-%d")); entry_from.pack()
tk.Label(f_right, text="По дату:").pack()
entry_to = tk.Entry(f_right); entry_to.insert(0, datetime.now().strftime("%Y-%m-%d")); entry_to.pack()

def export_csv():
    try:
        dt1 = int(datetime.strptime(entry_from.get(), "%Y-%m-%d").timestamp())
        dt2 = int((datetime.strptime(entry_to.get(), "%Y-%m-%d") + timedelta(days=1)).timestamp())
    except:
        print("❗ Неверный формат даты")
        return
    fn = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
    if not fn: return
    with open(fn, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["plate", "in", "out", "duration", "cost"])
        for r in db.execute("SELECT plate, time_in, time_out, duration, cost FROM visits WHERE time_out BETWEEN ? AND ?", (dt1, dt2)):
            w.writerow([r[0], fmt_time(r[1]), fmt_time(r[2]), r[3] // 60, r[4]])
tk.Button(f_right, text="Сформировать отчет", command=export_csv).pack(pady=10)

# История
tree = ttk.Treeview(root, columns=("plate", "in", "out", "dur", "cost"), show="headings", height=8)
for c, t in zip(("plate", "in", "out", "dur", "cost"), ("Номер", "Въезд", "Выезд", "Мин", "Сум")):
    tree.heading(c, text=t)
tree.pack(fill="both", expand=True)

lbl_total = tk.Label(root, text="Общая сумма за день: 0 сум", font=("Arial", 12))
lbl_total.pack(side="right", anchor="e", padx=10)
tk.Label(root, text="Разработчик: Александр +998 97 7333493", font=("Arial", 12)).pack(side="left", anchor="w", padx=10)

def update_history():
    tree.delete(*tree.get_children())
    for r in db.execute("SELECT plate, time_in, time_out, duration, cost FROM visits WHERE time_out IS NOT NULL ORDER BY id DESC LIMIT 10"):
        tree.insert("", "end", values=(r[0], fmt_time(r[1]), fmt_time(r[2]), r[3] // 60, r[4]))
    midnight = int(datetime.combine(datetime.now(), datetime.min.time()).timestamp())
    total = db.execute("SELECT SUM(cost) FROM visits WHERE time_out >= ? AND plate NOT IN (SELECT plate FROM whitelist)", (midnight,)).fetchone()[0] or 0
    lbl_total.config(text=f"Общая сумма за день: {total} сум")

def handle_client(conn, addr):
    buf = b""
    while True:
        data = conn.recv(65536)
        if not data: break
        buf += data
        if b"</config>" not in buf: continue
        xml = buf.decode(errors="ignore"); buf = b""
        ip = addr[0]
        t_raw = extract_tag(xml, "currentTime") or "0"
        ts = convert_ts_fixed(t_raw)

        for item in extract_all_items(xml):
            plate = extract_plate(item)
            if not plate or re.fullmatch(r"Т+", plate): continue
            b64 = extract_base64(item)
            if not b64: continue

            if ip == ENTRY_IP:
                p_in = save_img(b64, plate, "entry", ts)
                db.execute("INSERT INTO visits (plate, time_in, photo_in) VALUES (?, ?, ?)", (plate, ts, p_in))
                db.commit()
                lbl_in.config(text=f"{plate}\n{fmt_time(ts)}")
                img = ImageTk.PhotoImage(Image.open(p_in).resize((320,180)))
                canvas_in.image = img; canvas_in.create_image(0,0,anchor="nw",image=img)
                threading.Thread(target=open_gate, args=(ENTRY_IP,), daemon=True).start()

            elif ip == EXIT_IP:
                row = db.execute("SELECT id, time_in, photo_in FROM visits WHERE plate=? AND time_out IS NULL ORDER BY time_in DESC LIMIT 1", (plate,)).fetchone()
                if not row: continue
                visit_id, t_in, p_in = row
                dur = ts - t_in
                free_min = int(entry_free.get() or 5)
                price_hour = int(entry_price.get() or 15000)
                is_white = db.execute("SELECT 1 FROM whitelist WHERE plate=?", (plate,)).fetchone()
                cost = 0 if is_white else calc_cost(dur, free_min, price_hour)
                p_out = save_img(b64, plate, "exit", ts)
                db.execute("UPDATE visits SET time_out=?, photo_out=?, duration=?, cost=? WHERE id=?",
                           (ts, p_out, dur, cost, visit_id))
                db.commit()
                lbl_out.config(text=f"{plate}\nВъезд: {fmt_time(t_in)}\nВыезд: {fmt_time(ts)}\n{dur//60} мин | {cost} сум")
                btn_print.config(command=lambda: print_receipt(plate, t_in, ts, dur, cost))
                threading.Thread(target=print_receipt, args=(plate, t_in, ts, dur, cost), daemon=True).start()
                for can, imgp in [(canvas_in_mid, p_in), (canvas_out_mid, p_out)]:
                    img = ImageTk.PhotoImage(Image.open(imgp).resize((320,180)))
                    can.image = img; can.create_image(0,0,anchor="nw",image=img)
                update_history()
                if is_white:
                    threading.Thread(target=open_gate, args=(EXIT_IP,), daemon=True).start()
    conn.close()

def start_server():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    print(f"🚀 TCP сервер запущен на {HOST}:{PORT}")
    while True:
        c, a = s.accept()
        threading.Thread(target=handle_client, args=(c, a), daemon=True).start()

threading.Thread(target=start_server, daemon=True).start()
root.mainloop()
