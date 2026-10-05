import hashlib
import json
import os
import re
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from getpass import getpass
from pathlib import Path
from urllib import request

from playwright.sync_api import sync_playwright

STATE_FILE = Path("generic_monitor_state.json")
STOP_WORDS = {"the", "a", "an", "for", "to", "and", "or", "of", "in", "on", "tickets", "ticket"}


def now():
    return datetime.now().strftime("%H:%M:%S")


def prompt_configuration():
    print("\n--- Website monitor setup ---")
    url = input("Website URL: ").strip()
    description = input("What are you monitoring? (e.g. Solfest 2026 tickets): ").strip()
    keywords_input = input("Keywords that must appear, comma-separated (Enter to derive them): ").strip()

    if keywords_input:
        keywords = [item.strip().lower() for item in keywords_input.split(",") if item.strip()]
    else:
        keywords = [
            word.lower() for word in re.findall(r"[A-Za-z0-9]{3,}", description)
            if word.lower() not in STOP_WORDS
        ]

    if not url or not description or not keywords:
        raise ValueError("A URL, a description, and at least one keyword are required.")

    interval_input = input("Check every how many seconds? [120]: ").strip()
    interval = int(interval_input or "120")
    if interval < 30:
        raise ValueError("Use at least 30 seconds to avoid excessive requests.")

    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook:
        webhook = getpass("Discord webhook URL (hidden; Enter to skip): ").strip()

    return {
        "url": url,
        "description": description,
        "keywords": keywords,
        "interval": interval,
        "webhook": webhook,
    }


def wait_with_progress(seconds):
    width = 24
    for elapsed in range(seconds):
        remaining = seconds - elapsed
        filled = int((elapsed / seconds) * width)
        bar = "#" * filled + "." * (width - filled)
        print(f"\r[{now()}] Next check in {remaining:3d}s [{bar}]", end="", flush=True)
        time.sleep(1)
    print()


def relevant_text(body, keywords):
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    matches = []

    # Every keyword must appear in the same small block of page text.
    for index in range(len(lines)):
        window = lines[max(0, index - 5): index + 9]
        combined = "\n".join(window).lower()
        if all(keyword in combined for keyword in keywords):
            matches.extend(window)

    return "\n".join(dict.fromkeys(matches))


def page_snapshot(page, config):
    print(f"[{now()}] Checking {config['description']}...", flush=True)
    page.goto(config["url"], wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(3000)
    body = page.locator("body").inner_text()
    return relevant_text(body, config["keywords"])


def notify(config, details):
    message = f"Website update: {config['description']}\n{config['url']}\n\n{details[:1200]}"

    if config["webhook"]:
        try:
            payload = json.dumps({"content": message}).encode()
            webhook_request = request.Request(
                config["webhook"],
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            request.urlopen(webhook_request, timeout=10)
        except Exception as error:
            print(f"[{now()}] Discord alert failed: {error}", flush=True)

    if sys.platform == "darwin":
        subprocess.run([
            "osascript", "-e",
            'display notification "Website update detected. Check your browser." with title "Website monitor" sound name "Glass"',
        ])
        subprocess.run(["say", "Website update detected. Check your browser now."])
    elif sys.platform == "win32":
        import winsound
        winsound.MessageBeep()

    webbrowser.open(config["url"])


def fingerprint(text):
    return hashlib.sha256(text.encode()).hexdigest()


def monitor_id(config):
    identity = config["url"] + "|" + "|".join(config["keywords"])
    return hashlib.sha256(identity.encode()).hexdigest()


def main():
    config = prompt_configuration()
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"monitors": {}}
    state.setdefault("monitors", {})
    identifier = monitor_id(config)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            while True:
                try:
                    details = page_snapshot(page, config)
                    previous = state["monitors"].get(identifier)

                    if previous is None:
                        state["monitors"][identifier] = {
                            "fingerprint": fingerprint(details) if details else None,
                        }
                        STATE_FILE.write_text(json.dumps(state, indent=2))
                        print(f"[{now()}] Baseline saved. Waiting for a real update.", flush=True)
                    elif not details:
                        print(f"[{now()}] Target keywords are not on the page yet.", flush=True)
                    else:
                        current = fingerprint(details)
                        if current != previous["fingerprint"]:
                            print("\nMatching page content changed.\n", flush=True)
                            print(details + "\n", flush=True)
                            notify(config, details)
                            previous["fingerprint"] = current
                            STATE_FILE.write_text(json.dumps(state, indent=2))
                        else:
                            print(f"[{now()}] No relevant change.", flush=True)

                except Exception as error:
                    print(f"[{now()}] Check failed: {error}", flush=True)

                wait_with_progress(config["interval"])
        finally:
            browser.close()


if __name__ == "__main__":
    main()
