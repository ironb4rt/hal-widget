# KONTRAKT — jak aplikacja pobiera treści

Etap 1 jest maksymalnie prosty: aplikacja to WebView ładujący **jeden URL** podany
w konfiguracji (MainActivity → pole URL). Cała inteligencja po stronie tego URL-a.

## Co serwuje Hal

- **Panel HTML** (jeden dokument): raporty, wykresy (SVG/płytki PNG), fragmenty artykułów,
  mini-czat. Aplikacja nie interpretuje treści — renderuje cokolwiek tam trafi.
- Odświeżanie: pull-to-refresh w WebView, reload przy włączeniu ekranu.

## WIZJA PANELU (Bartek, 09.10) — „żywe, nowoczesne, proste"

Panel to dynamiczna wizualizacja naszej interakcji, układ stałych elementów:

- **Róg 1 (stały):** ceny surowców (źródła z [[agent-surowce]]: Westmetall/LME),
  odświeżane przy każdym włączeniu ekranu.
- **Róg 2 (stały):** ikona Hal z animacjami zależnymi od trybu (idle / myślenie / nowa
  wiadomość / alert).
- **Tło:** odzwierciedlenie aktualnej pogody (darmowe API, np. open-meteo, bez klucza).
- **Elementy ruchome:** temperatura, rotujące newsy, okresowe updatey o śledzonych akcjach
  (tickery z [[agent-portfel]]).

Ograniczenie baterii obowiązujące mimo wszystkiego: animacje CSS/JS wyłącznie gdy ekran
włączony i panel widoczny (pauza przez WebView.onPause już zaimplementowana w usłudze);
tickery rotowane transformami CSS (bez pętli JS), przygaszone gdy okno bez interakcji >2 min.
tickery rotowane transformami CSS (bez pętli JS), przygaszone gdy okno bez interakcji >2 min.

## Etap 2 (kontrakt na przyszłość, nieaktywny)

JSON manifest treści, np.:

```json
{
  "version": 1,
  "panel_url": "https://.../panel.html",
  "last_report": { "title": "Raport surowce 09.10", "url": "https://.../raport.html" },
  "unread": 2
}
```

Aplikacja pobiera manifest przy włączeniu ekranu, pokazuje badge na oknie, tap → panel.

## Bezpieczeństwo (etap 1: minimum, etap 3: docelowo)

- URL panelu zawiera losowy token w ścieżce (prywatność przez nieprawdopodobieństwo).
- Etap 3: HTTPS + token w nagłówku, ewentualnie pinning certyfikatu.

---

## ZREALIZOWANE 10.10 — panel etapu 1 stoi

Panel jest gotowy i **działa na prawdziwych danych**. Leży w projekcie aplikacji:

```
android/app/src/main/assets/panel/
├── panel.html        # cały panel: tło pogodowe, kafle, rotator, ikona Hal
├── panel_data.json   # dane (generowane, wersjonowane)
├── fetch_data.py     # zbieracz: open-meteo + CoinGecko + Westmetall + NBP/Frankfurter
└── odswiez.sh        # ./odswiez.sh [--serve] — odśwież dane / podejrzyj w przeglądarce
```

Aplikacja ładuje panel **domyślnie z APK** (`file:///android_asset/panel/panel.html`).
Pole URL w konfiguracji nadal działa i nadpisuje wbudowany panel; przycisk
„Użyj wbudowanego panelu" czyści URL i wraca do wersji z APK.

### Co panel pokazuje

| Element | Źródło | Odświeżanie |
|---|---|---|
| Tło (gradient + słońce/księżyc/deszcz/mgła) | open-meteo, kod WMO | przy wczytaniu |
| Kafel „Pogoda" (temp, min/max, wiatr, wilgotność) | open-meteo, Bielsko-Biała | przy wczytaniu |
| Kafel „Surowce" (srebro USD/oz, miedź USD/lb, aluminium USD/lb, HRC US USD/lb) | Yahoo v8 (SI=F, HG=F, ALI=F) + HRC z dziennego raportu surowcowego | klientowo: pogoda/krypto/fx co godzinę + przy włączeniu ekranu; surowce z panel_data.json (godzinny harmonogram po stronie Hala, `75add24b`; CORS Yahoo blokuje pobór z telefonu — tryb `?src=<URL>` łączy to z GitHubem) |
| Kafel „Krypto" (BTC/ETH w USD i PLN, zmiana 24 h) | CoinGecko | przy wczytaniu |
| Rotator (8 pozycji) | wszystkie powyżej + USD/PLN | co 6 s, tylko gdy widoczny |
| Ikona Hal: spoczynek / myślenie / nowa wiadomość / alert | sterowana z JS | zdarzeniowo |

### Ikona Hal — jak przełączać tryby

```js
setMode("idle")      // spoczynek  — mruganie oczu
setMode("thinking")  // myślenie   — obracający się pierścień + oddech
setMode("message")   // nowa wiadomość — pulsujące kółko + drgnięcie
setMode("alert")     // alert      — czerwona poświata, białe oczy
```

Podglądowo: `panel.html?mode=thinking`. Docelowo etap 3 podstawi to pod stan
faktyczny (nowa wiadomość z AgentMail, alert z bota).

### Dyscyplina baterii — co jest zrobione

- Animacje wyłącznie CSS; jedyny `setInterval` to rotator (6 s) i on **pauzuje**
  przy `document.hidden` (aplikacja pauzuje WebView przy zgaszonym ekranie).
- Brak websocketu, brak długiego pollingu. Odświeżanie danych co 10 min tylko
  gdy strona widoczna, plus reload przy włączeniu ekranu.
- Przygaszenie (opacity .38, odbarwienie) po **2 min** bez dotyku/scrolla;
  dowolna interakcja natychmiast przywraca.

### Odporność na awarie źródeł

`fetch_data.py` traktuje każde źródło osobno. Jeśli jedno padnie, zapisuje
ostatnią znaną wartość z poprzedniego `panel_data.json` i oznacza ją
`"stale": true`; panel pokazuje wtedy bursztynowe ostrzeżenie w stopce
i przechodzi w tryb „alert". Brak danych nigdy nie wywala panelu do pustki.

### Czego panel jeszcze nie ma (świadomie)

- **Newsów** — rotator jest, treści z RSS nie ma. Czeka na decyzję, które źródła
  (i czy w ogóle) mają trafiać do panelu.
- **Akcji z portfela** — kafel jest przygotowany, brakuje źródła notowań GPW/US
  bez klucza (Stooq odrzuca ruch z naszego egressu — sprawdzone 10.10).
- **Mini-czatu** — etap 3.
