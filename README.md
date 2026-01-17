# 🌅 Zorin Auto Theme Changer
Automatically switch between light and dark themes in **Zorin OS Core Edition(Gnome)** based on **sunrise** and **sunset** times. Compatible with both **X11** and **Wayland** sessions.


## ✨ Features
 
- 📍 **Flexible Location Options:**
  1. **Manual coordinates** for  **✅100% offline** use (recommended) 
  2. **Auto-detect** your location via **IP address** (fallback)
- ⚙️ **Lightweight & simple** – just run it and forget it
- ⏱️ **No background activity** - only runs at the scheduled time
- 🕐 **Automatic Theme Switching** – changes your Zorin theme at local **sunrise** and **sunset**. 


## 🤝 Contribute

Any help is **highly appreciated** 🙌  
Bug reports, feature requests, and pull requests are always welcome!


## 🛠 Setup
1. Download the script from the release page and save it to your desired location.
2. Open a terminal in that location and install the required dependencies.
### Zorin OS 18
```bash
sudo apt install python3-astral python3-tz 
```
### Zorin OS 17
```bash
sudo apt install python3-pip
pip install astral
```
3. Finally, run the script:
```bash
python3 ZorinAutoThemeChanger.py 
```
