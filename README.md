# Hal Widget — okno Hal na Androidzie

Cel: pływające, interaktywne okno (overlay) na ekranie telefonu, w którym Hal wyświetla raporty,
wizualizacje, fragmenty artykułów i odpowiada na pytania. Aplikacja to cienka skorupa (WebView);
cała treść i logika siedzą po stronie Hal.

## Architektura (etap 1)

- **Aplikacja Android** (`android/`): usługa pierwszego planu z WebView w oknie overlay
  (SYSTEM_ALERT_WINDOW). Okno można przeciągać, zmieniać rozmiar, zamykać.
- **Dyscyplina baterii:** WebView pauzowany przy zgaszonym ekranie, brak websocketu i timera
  w tle, treść odświeżana przy włączeniu ekranu + pull-to-refresh. Zero animacji w tle.
- **Treść:** aplikacja ładuje URL podany w konfiguracji (etap 1: panel HTML serwowany przez
  Hal). Format i polityka cache → `backend/KONTRAKT.md`.
- **Push (opcjonalnie, etap 3):** FCM — tylko jeśli etap 1 działa i będziemy chcieli
  natychmiastowych powiadomień przy zgaszonym ekranie.

## Pliki

- `INSTRUKCJA-KROK-PO-KROKU.md` — pełna instrukcja dla Ciebie (instalacja narzędzi, build APK,
  instalacja na telefonie). Zacznij tutaj.
- `ARCHITEKTURA.md` — decyzje projektowe, polityka baterii, mapa drogowa.
- `android/` — kompletny projekt Android Studio (Kotlin, bez zewnętrznych zależności).
- `backend/KONTRAKT.md` — jak aplikacja pobiera treści, przykładowy JSON.

## Status

Kod napisany, ale jeszcze NIESKOMPILOWANY — pierwszy build wyłapie drobne poprawki,
które Hal naniesie po wynikach. Etap 2 (widget na pulpicie) i etap 3 (FCM) po etapie 1.

**Panel treści stoi (10.10):** `android/app/src/main/assets/panel/` — `panel.html`
z żywymi danymi (pogoda, LME, krypto, rotator, ikona Hal w czterech trybach),
`fetch_data.py` jako zbieracz i `odswiez.sh` do odświeżania. Aplikacja ładuje go
domyślnie z APK, bez serwera i bez sieci. Szczegóły → `backend/KONTRAKT.md`.
