#!/usr/bin/env python3
"""Push panel_data.json do GitHub (ironb4rt/hal-widget) przez Contents API.

Rozszerzenie godzinowego cyklu danych: schedule 75add24b o :20 generuje
świeże panel_data.json, ten skrypt o :25 wysyła go do repo, jeśli się zmienił.
Telefon z polem URL ustawionym na raw.githubusercontent.com/.../panel_data.json
(?src=) dostaje więc nowe surowce/wiadomości bez reinstalacji APK.

Token: sejf asystenta, github/hal_widget_pat (Contents: RW). Żadnych sekretów
w plikach repo.
"""
import base64
import json
import subprocess
import sys
import urllib.request

REPO = "ironb4rt/hal-widget"
PATH = "android/app/src/main/assets/panel/panel_data.json"
JSON_LOKALNIE = "/workspace/hal-widget/android/app/src/main/assets/panel/panel_data.json"
UA = "Hal-Widget-Pusher/1.0"


def token() -> str:
    out = subprocess.run(
        ["assistant", "credentials", "reveal", "--service", "github",
         "--field", "hal_widget_pat"],
        capture_output=True, text=True, timeout=60)
    lines = [l.strip() for l in out.stdout.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def api(url: str, tok: str, method: str = "GET", payload: dict | None = None):
    req = urllib.request.Request(url, method=method, headers={
        "Authorization": f"Bearer {tok}",
        "User-Agent": UA,
        "Accept": "application/vnd.github+json",
    })
    body = None
    if payload is not None:
        body = json.dumps(payload).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=body, timeout=60) as r:
        return json.loads(r.read().decode())


def main() -> int:
    tok = token()
    if not tok:
        print("BRAK TOKENA: pusty reveal github/hal_widget_pat")
        return 1

    with open(JSON_LOKALNIE, "rb") as f:
        nowa_tresc = f.read()

    url = f"https://api.github.com/repos/{REPO}/contents/{PATH}"
    obecny = api(url, tok)
    if base64.b64decode(obecny["content"]) == nowa_tresc:
        print("Bez zmian — pomijam push.")
        return 0

    api(url, tok, "PUT", {
        "message": "dane godzinne: surowce + wiadomosci",
        "content": base64.b64encode(nowa_tresc).decode(),
        "sha": obecny["sha"],
    })
    print(f"Push OK ({len(nowa_tresc)} B).")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"BLAD: {e}")
        sys.exit(1)
