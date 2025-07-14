📡 TCP Image Receiver
This Python script implements a simple multi-threaded TCP server that listens for incoming XML packets, extracts base64-encoded images and metadata, decodes and saves the images, and logs useful information to the console.

🚀 What does it do?
✅ Listens on a specified IP and port (192.168.226.222:18000 by default)
✅ Receives XML data containing:

Base64-encoded image data
MAC address of the sender
Timestamp or other tags

✅ Extracts <![CDATA[...]]> sections and plain XML tags
✅ Saves decoded images as .jpg files in the images/ directory
✅ Generates unique filenames with a counter, MAC address, and timestamp
✅ Prints the SHA256 hash of each received packet for integrity checking
✅ Handles multiple clients simultaneously using threads

⚙️ How it works
A TCP client (e.g., a camera) connects and sends XML data.
The server reads the data in chunks (BUFFER_SIZE = 64 KB).
When it detects </config>, it processes the full XML.

It extracts:

<sourceBase64Data><![CDATA[...] ]]> → The image

<mac><![CDATA[...] ]]> → The sender’s MAC address

<currentTime> → The timestamp

It decodes the image and saves it to images/.

The connection stays alive until the client disconnects.

📂 Directory structure
images/ — All decoded images are saved here.
face-detect.py — The main Python script.

🏷️ How to run
Make sure Python 3 is installed.
Save the script as face-detect.py.

Install any dependencies (only hashlib, socket, threading — all built-in!).

Run the server:

python face-detect.py
To stop the server, press Ctrl+C.

🔐 Notes
Make sure your firewall allows incoming TCP connections on the specified port.
Update HOST and PORT if needed.
Images are named like image_0_MAC_TIMESTAMP.jpg.

📌 Use cases
Receiving snapshots from IP cameras.
Debugging IoT devices that send images over TCP.
Testing base64 image pipelines.

✨ Example log

MSG start TCP server successfully on 192.168.226.222:18000

('192.168.226.100', 54032) connected

[TCP] ('192.168.226.100', 54032)
MAC: AA:BB:CC:DD:EE:FF
Time: 1720688894000
SHA256: 1f6d2a7e0d45c0b...
Base64 length: 234567
[✔] Saved: images/image_0_AA_BB_CC_DD_EE_FF_20250709_132812.jpg

('192.168.226.100', 54032) disconnected
