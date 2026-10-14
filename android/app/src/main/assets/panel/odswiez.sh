#!/usr/bin/env bash
# Odświeżenie danych panelu Hal Widget.
#
# Uruchamia fetch_data.py i kopiuje wynik do assets APK. Po uruchomieniu
# wystarczy przebudować APK (lub, przy panelu serwowanym z sieci, wgrać
# panel_data.json na serwer).
#
#   ./odswiez.sh            # dane do assets
#   ./odswiez.sh --serve    # dodatkowo lokalny serwer podglądowy na :8080
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"

python3 "$HERE/fetch_data.py" --out "$HERE/panel_data.json"

if [ "${1:-}" = "--serve" ]; then
  echo "podgląd: http://localhost:8080/panel.html  (Ctrl+C kończy)"
  cd "$HERE" && python3 -m http.server 8080
fi
