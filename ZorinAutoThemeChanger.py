import requests
from astral import LocationInfo
from astral.sun import sun
from datetime import datetime, date
import pytz
import subprocess
import time

def get_manual_location():
    latitude = 26.480730  
    longitude = 89.526649  
    timezone = "Asia/Kolkata"   

    if None not in (latitude, longitude, timezone):
        return latitude, longitude, timezone
    else:
        return None

def get_location():
    manual = get_manual_location()
    if manual:
        print("📍 Using manually set location...")
        return manual

    print("🌐 Fetching location from IP...")
    try:
        res = requests.get("https://ipinfo.io/json", timeout=5)
        res.raise_for_status()
        data = res.json()
        lat, lon = map(float, data['loc'].split(','))
        return lat, lon, data['timezone']
    except Exception as e:
        print(f"❌ Failed to get location from IP: {e}")
        exit(1)

def get_sun_times(lat, lon, timezone):
    city = LocationInfo(name="Local", region="Here", latitude=lat, longitude=lon)
    s = sun(city.observer, date=date.today(), tzinfo=timezone)
    return s['sunrise'], s['sunset']

def get_current_variant():
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True, text=True, check=True
        )
        theme = result.stdout.strip().strip("'")
        if "-" in theme:
            return theme.split("-")[0]  
        else:
            return theme
    except Exception as e:
        print(f"❌ Failed to detect current theme variant: {e}")
        return "ZorinBlue"  

def set_zorin_theme(mode):
    variant = get_current_variant()
    if mode == "light":
        theme = f"{variant}-Light"
        color_scheme = "default"
    elif mode == "dark":
        theme = f"{variant}-Dark"
        color_scheme = "prefer-dark"
    else:
        print("⚠️ Invalid mode. Use 'light' or 'dark'.")
        return

    commands = [
        ["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", theme],
        ["gsettings", "set", "org.gnome.desktop.interface", "icon-theme", theme],
        ["gsettings", "set", "org.gnome.shell.extensions.user-theme", "name", theme],
        ["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", color_scheme]
    ]

    for cmd in commands:
        subprocess.run(cmd)

def is_correct_theme_applied(mode, current_variant):
    expected = f"{current_variant}-Light" if mode == "light" else f"{current_variant}-Dark"
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True, text=True, check=True
        )
        current_theme = result.stdout.strip().strip("'")
        return current_theme == expected
    except Exception:
        return False

def main():
    lat, lon, timezone = get_location()
    sunrise, sunset = get_sun_times(lat, lon, timezone)
    now = datetime.now(pytz.timezone(timezone))
    current_variant = get_current_variant()

    print(f"🌅 Sunrise: {sunrise.strftime('%H:%M')}")
    print(f"🌇 Sunset:  {sunset.strftime('%H:%M')}")
    print(f"🕒 Now:     {now.strftime('%H:%M')}")
    print(f"🎨 Current Zorin Theme Variant: {current_variant}")

    if sunrise < now < sunset:
        print("🌞 It's daytime")
        if not is_correct_theme_applied("light", current_variant):
            print("Switching to light theme.")
            set_zorin_theme("light")
        else:
            print("Light theme already applied.")
    else:
        print("🌙 It's nighttime")
        if not is_correct_theme_applied("dark", current_variant):
            print("Switching to dark theme.")
            set_zorin_theme("dark")
        else:
            print("Dark theme already applied.")

if __name__ == "__main__":
    main()

