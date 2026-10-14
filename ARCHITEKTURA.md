# ARCHITEKTURA — Hal Widget

## Decyzja technologiczna

Wybrany wariant: **overlay (SYSTEM_ALERT_WINDOW) z WebView w usłudze pierwszego planu**.
Powód: pełna funkcjonalność wyświetlania (HTML, wykresy, formularze, czat) przy najniższym
koszcie utrzymania — treść przygotowuje Hal, aplikacja jest skorupą.

Odrzucone: klasyczny AppWidget (za mało funkcjonalny: RemoteViews nie ma dowolnej kanwy),
natywne widoki w overlay (każdy element pisany ręcznie, wolny rozwój).

## Polityka baterii — trzy twarde zasady

1. **Przy zgaszonym ekranie aplikacja nie robi NIC.** BroadcastReceiver na
   `ACTION_SCREEN_OFF` wstrzymuje WebView (`onPause()`) i ewentualne pobieranie;
   `ACTION_SCREEN_ON` wznawia i odświeża treść. To główna przesłanka szacunku
   ~1–2% baterii na dobę.
2. **Brak websocketu i długiego pollingu.** Odświeżanie: przy włączeniu ekranu,
   pull-to-refresh oraz opcjonalny WorkManager co ≥15 minut (min. okres WorkManagera).
   FCM dopiero w etapie 3, jeśli powstanie potrzeba „natychmiast" przy zgaszonym ekranie.
3. **Zero animacji w tle.** Okno renderuje tylko wtedy, gdy jest widoczne i ekran włączony.

## Komponenty aplikacji

| Plik | Rola |
|---|---|
| `MainActivity.kt` | Ekran konfiguracji: URL treści, start/zatrzymanie okna, przycisk nadania uprawnienia overlay |
| `OverlayService.kt` | Usługa FGS: tworzy okno WindowManagera z WebView, obsługa przeciągania i rozmiaru |
| `ScreenReceiver.kt` | Pauza/wznów przy zgaszaniu/włączaniu ekranu |
| `BootReceiver.kt` | Autostart usługi po restarcie telefonu (jeśli była włączona) |
| `ContentFetcher.kt` | Pobranie JSON konfiguracji/manifestu treści + cache offline |

## Uprawnienia, o które poprosi system

- `SYSTEM_ALERT_WINDOW` — nadawane ręcznie: Ustawienia → Wyświetlanie nakładek
  (aplikacja ma przycisk, który otworzy właściwe ustawienie).
- `POST_NOTIFICATIONS` — Android 13+ wymaga zgody na powiadomienie usługi FGS.
- `INTERNET`, `FOREGROUND_SERVICE`, `RECEIVE_BOOT_COMPLETED` — standard, bez zgody.

## Mapa drogowa

- **Etap 1 (teraz):** okno overlay z WebView, drag/resize, konfiguracja URL, dyscyplina
  baterii. Build ręczny u Bartka.
- **Etap 2:** widget na pulpicie (Glance): kafel z ostatnią wiadomością, tap → pełne okno.
- **Etap 3:** FCM push + interakcja dwukierunkowa (pisanie do Hal z poziomu okna).
- **Etap 4 (opcja):** certyfikat APK pinning / lokalny build bez sieci dla pełnej prywatności.

## Otwarte pytania (rozstrzygnie użycie)

- Domyślny rozmiar i pozycja okna (propozycja: 340×480 dp, prawy górny róg, 24 dp margines).
- Czy okno ma być nad klawiaturą, czy chować się przy otwieraniu klawiatury.
- Ciemny/jasny motyw panelu treści (decyduje HTML, nie aplikacja).
