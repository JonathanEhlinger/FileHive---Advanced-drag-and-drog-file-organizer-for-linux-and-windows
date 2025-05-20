README.md
# 🐝 FileHive
Created by Jonathan Ehlinger 5/20/25
> **Smart file organization, compression, and encryption software built for power users and digital chaos.**  
> For Windows only – supports drag & drop, intelligent sorting, and right-click context actions.

---

## ⚙️ Features

- 🔄 **Drag-and-drop up to 10TB** of data (USB, cloud-sync folders, local)
- 🧠 **Auto-organize by type & date**  
  - Example: `/Pictures/2024-07/*.jpg`, `/Documents/2025-01/*.docx`
- 📝 **Auto-generate TXT notes** inside folders  
  - Includes metadata, summaries, and cross-references for similar-date files
- 🔍 **Smart Search**: Quickly find organized content by type, folder, or date
- 🔐 **AES-256 Encryption Options**  
  - Full folders or selected file types (e.g., `.txt`, `.jpg`)
- 🗜️ **ZIP Compression** with customizable folder depth
- 🖱️ **Right-Click Explorer Integration**  
  - Encrypt, Compress, or Organize directly from File Explorer
- 📤 **Export Options**: USB, local drives, and Bluetooth transfer

---

## 🏗️ Tech Stack

| Component      | Tool/Library         |
|----------------|----------------------|
| UI Framework   | PyQt5 (or Tkinter)   |
| Language       | Python 3.x           |
| Compression    | `zipfile`, `shutil`  |
| Encryption     | `cryptography`       |
| Bluetooth      | `pybluez` (Windows)  |
| File Indexing  | SQLite + JSON Logs   |

---

## 🔧 Installation

```bash
git clone https://github.com/yourusername/filehive.git
cd filehive
pip install -r requirements.txt
python main.py
