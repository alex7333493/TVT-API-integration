This Python script subscribes to motion detection or other event notifications from an IP camera using HTTP.

📌 What does this script do?
Sends a POST request to the camera to set up an event subscription (e.g., motion alarm or object detection).
Keeps the connection alive to receive real-time event notifications.
Saves the last received raw XML to last_raw_event.xml.
Parses key information from the XML: object name, identification number, and timestamp.
Converts the raw timestamp to a human-readable date and time.
Runs continuously until stopped manually (Ctrl+C).

⚙️ Tech stack
http.client — for HTTP communication.
base64 — for Basic Authentication.
xml.etree.ElementTree — for XML parsing.
datetime — for timestamp formatting.

🏷️ How to run it?
Make sure the camera is accessible at the specified IP and port (192.168.226.201:8080).

Update the login and password if needed (admin:P@rol123 by default).

Run the script:
python file.py
Stop anytime with Ctrl+C.

⚡ Use cases
Ideal for:
Integrating IP cameras with external systems.
Logging motion or alarm events.
Prototyping video analytics or access control systems.



Этот Python-скрипт выполняет подписку на события движения или другие уведомления от IP-камеры по протоколу HTTP.

📌 Что делает скрипт?
Отправляет POST-запрос на камеру для настройки подписки на события (например, тревога или распознавание).
Поддерживает соединение и принимает события в режиме реального времени.
Автоматически сохраняет последний полученный сырой XML (last_raw_event.xml).
Извлекает ключевую информацию из события: имя объекта, идентификатор и метку времени.
Преобразует временную метку в читаемый формат.
Работает до ручного прерывания (Ctrl+C).

⚙️ Что используется?
http.client — для HTTP-запросов.
base64 — для базовой авторизации.
xml.etree.ElementTree — для разбора XML.
datetime — для форматирования времени.

🏷️ Как запустить?
Проверь, что камера доступна по IP и порту (192.168.226.201:8080).

Обнови логин и пароль (по умолчанию admin:P@rol123).

Запусти:

python file.py

Остановить: Ctrl+C.


⚡ Для чего это нужно?
Подходит для:

Интеграции камер с внешними системами.
Логирования тревожных событий.
Прототипирования системы видеоаналитики.

