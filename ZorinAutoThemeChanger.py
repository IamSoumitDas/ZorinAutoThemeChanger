#!/usr/bin/env python3
import requests
from astral import LocationInfo
from astral.sun import sun
from datetime import datetime, date, timedelta
import pytz
import subprocess
import os
import sys
from pathlib import Path


if len(sys.argv) > 1 and sys.argv[1] in ("--light", "--dark"):
    MODE_OVERRIDE = sys.argv[1][2:]
else:
    MODE_OVERRIDE = None

UNIT_BASENAME = "zorin-auto-theme"
USER_SYSTEMD_DIR = Path.home() / ".config/systemd/user"
SERVICE_PATH = USER_SYSTEMD_DIR / f"{UNIT_BASENAME}.service"
TIMER_PATH = USER_SYSTEMD_DIR / f"{UNIT_BASENAME}.timer"


def get_manual_location():
    # Set your coordinates/timezone here if you prefer manual config
    latitude = None
    longitude = None
    timezone = None
    if None not in (latitude, longitude, timezone):
        return latitude, longitude, timezone
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
        lat, lon = map(float, data["loc"].split(","))
        tzname = data["timezone"]
        return lat, lon, tzname
    except Exception as e:
        print(f"❌ Failed to get location from IP: {e}")
        sys.exit(1)

def astral_sun_times(lat, lon, tzname, for_date):
    tz = pytz.timezone(tzname)
    city = LocationInfo(name="Local", region="Here", timezone=tzname, latitude=lat, longitude=lon)
    try:
        s = sun(city.observer, date=for_date, tzinfo=tz)
        return s["sunrise"], s["sunset"]
    except Exception:
        noon = tz.localize(datetime(for_date.year, for_date.month, for_date.day, 12, 0, 0))
        return noon, noon

def get_today_tomorrow_events(lat, lon, tzname):
    today = date.today()
    tz = pytz.timezone(tzname)
    sunrise_today, sunset_today = astral_sun_times(lat, lon, tzname, today)
    sunrise_tom, sunset_tom = astral_sun_times(lat, lon, tzname, today + timedelta(days=1))
    now = datetime.now(tz)

    if sunrise_today < now < sunset_today:
        current_mode = "light"
        next_time = sunset_today
        next_label = "sunset"
    else:
        current_mode = "dark"
        next_time = sunrise_today if now < sunrise_today else sunrise_tom
        next_label = "sunrise"

    return current_mode, next_label, next_time, (sunrise_today, sunset_today), (sunrise_tom, sunset_tom)

def get_current_gtk_theme():
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip().strip("'")
    except Exception:
        return ""

def choose_theme_name(base_theme, mode):
    if base_theme.lower().startswith("adwaita"):
        return "Adwaita-dark" if mode == "dark" else "Adwaita"
    root = base_theme.split("-")[0] if "-" in base_theme else base_theme
    return f"{root}-Dark" if mode == "dark" else f"{root}-Light"

def set_theme(mode):
    base = get_current_gtk_theme() or "ZorinBlue"
    theme = choose_theme_name(base, mode)
    color_scheme = "prefer-dark" if mode == "dark" else "default"

    cmds = [
        ["gsettings", "set", "org.gnome.desktop.interface", "gtk-theme", theme],
        ["gsettings", "set", "org.gnome.desktop.interface", "color-scheme", color_scheme],
    ]
    for cmd in cmds:
        subprocess.run(cmd)
    try:
        subprocess.run(
            ["gsettings", "set", "org.gnome.shell.extensions.user-theme", "name", theme],
            check=True
        )
    except subprocess.CalledProcessError:
        pass

def is_correct_theme(mode):
    expected = choose_theme_name(get_current_gtk_theme() or "ZorinBlue", mode)
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
            capture_output=True, text=True, check=True
        )
        current_theme = result.stdout.strip().strip("'")
        return current_theme == expected
    except Exception:
        return False


def ensure_user_systemd_dir():
    USER_SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)

def write_service_if_missing():
    service_content = f"""[Unit]
Description=Zorin Auto Theme (apply and reschedule)
After=default.target

[Service]
Type=oneshot
ExecStart=/usr/bin/env python3 {os.path.abspath(__file__)}
"""
    if not SERVICE_PATH.exists():
        with open(SERVICE_PATH, "w") as f:
            f.write(service_content)

def write_timer(trigger_dt, tzname):
    oncalendar = f"{trigger_dt.strftime('%Y-%m-%d %H:%M:%S')} {tzname}"
    timer_content = f"""[Unit]
Description=Run Zorin Auto Theme at next event ({trigger_dt.strftime('%Y-%m-%d %H:%M %Z')})

[Timer]
OnCalendar={oncalendar}
AccuracySec=1min
Persistent=true

[Install]
WantedBy=timers.target
"""
    with open(TIMER_PATH, "w") as f:
        f.write(timer_content)

def update_timer(trigger_dt, tzname):
    now = datetime.now(pytz.timezone(tzname))
    if trigger_dt <= now:
        trigger_dt = now + timedelta(minutes=2)

    ensure_user_systemd_dir()
    write_service_if_missing()

    subprocess.run(["systemctl", "--user", "stop", f"{UNIT_BASENAME}.timer"])
    subprocess.run(["systemctl", "--user", "disable", f"{UNIT_BASENAME}.timer"])
    if TIMER_PATH.exists():
        try:
            TIMER_PATH.unlink()
        except Exception:
            pass

    write_timer(trigger_dt, tzname)

    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
    subprocess.run(["systemctl", "--user", "enable", "--now", f"{UNIT_BASENAME}.timer"], check=False)
    print(f"✅ Scheduled next run at {trigger_dt.strftime('%Y-%m-%d %H:%M:%S %Z')}")

def main():
    lat, lon, tzname = get_location()

    if MODE_OVERRIDE in ("light", "dark"):
        set_theme(MODE_OVERRIDE)
        _, _, next_time, _, _ = get_today_tomorrow_events(lat, lon, tzname)
        update_timer(next_time, tzname)
        print(f"🌟 Mode override applied: {MODE_OVERRIDE}")
        return

    current_mode, next_label, next_time, _, _ = get_today_tomorrow_events(lat, lon, tzname)
    if not is_correct_theme(current_mode):
        set_theme(current_mode)
        print(f"🎨 Applied {current_mode} mode based on sun position")
    else:
        print(f"ℹ️ {current_mode} mode already active")

    update_timer(next_time, tzname)

if __name__ == "__main__":
    main()

