# Event Ticket Monitor

A configurable Python script that checks a webpage for changes to text near chosen keywords.

Built while applying scripting lessons from AfricaHackon to a practical problem: keeping up with event ticket announcements.

## Features

- Interactive setup for a URL, monitoring description, keywords, and interval
- Browser-based page loading with Playwright
- Saved baselines for different URL and keyword combinations
- Terminal status messages and a countdown between checks
- Optional Discord webhook alerts
- Opens the monitored page when a change is detected
- macOS speech and desktop notifications
- Windows notification beep

## Installation

Requires Python 3.9 or later.

### macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
python reusable_monitor.py
```

To prevent idle sleep while monitoring:

```bash
caffeinate -i python reusable_monitor.py
```

Keep your MacBook lid open and its internet connection active.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe reusable_monitor.py
```

Windows-specific alert handling is included but has not yet been tested on Windows. Configure Windows power settings to prevent sleep while monitoring; Task Scheduler alone does not keep the computer awake.

## Usage

Enter:

1. The full webpage URL, including https://
2. A description of what you are watching
3. Comma-separated keywords
4. The interval in seconds (default: 120)
5. An optional Discord webhook URL

The description labels the monitor. The keywords determine which nearby text it compares.

For example:

- Description: Detty Dezemba tickets
- Keywords: detty, dezemba
- Interval: 120

The first successful check saves a baseline without sending an alert. Later checks alert when matching text appears or changes.

Press Control+C to stop.

## Discord

Provide the webhook at the hidden prompt, or set the DISCORD_WEBHOOK_URL environment variable.

The script does not save the webhook in its baseline file. Keep webhook URLs private and out of GitHub.

## How matching works

The script searches small windows of visible page text for all supplied keywords, then compares the matching text with its saved fingerprint.

This is a text-change monitor. An alert is a reason to inspect the page, not confirmation that tickets are available.

## Limitations

- Monitors one URL per running instance.
- Only checks the supplied page; it does not search an entire website.
- Does not click ticket-selection pop-ups or log in.
- Nearby unrelated text can cause false alerts.
- Changes outside the matching text, including link-only changes, may be missed.
- Keyword disappearance does not currently trigger an alert.
- A saved baseline does not prove that ticket details were captured.
- Page loading, network delays, and blocked requests can affect detection.
- Failed Discord deliveries are reported but are not currently queued for retry.
- Prompts must be answered again after restarting.

## Testing so far

Manually tested on macOS for page loading, baseline storage, and local alerts using a forced baseline mismatch.

That test verifies the alert path; it does not prove every ticket-status change will be detected.

## Local files

generic_monitor_state.json stores the saved baselines. It is excluded from Git along with virtual environments, environment files, and Python caches.
