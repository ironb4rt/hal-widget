# INSTRUKCJA KROK PO KROKU — pierwszy build Hal Widget

Dla kogo: dla Ciebie, jeśli dawno nie dotykałeś narzędzi deweloperskich. Wszystko co robisz
to: zainstalować Android Studio, otworzyć folder `android/`, kliknąć Build. Reszta to kliki
w interfejsie. Zaplanuj na to ~45 minut pierwszym razem.

## Część A — narzędzia (jednorazowo, ~30 min)

1. **Zainstaluj Android Studio** (wersja „Ladybug" lub nowsza):
   https://developer.android.com/studio
   - Instalator Windows domyślnie zainstaluje też JDK — zgódź się na wszystko domyślnie.
   - Przy pierwszym uruchomieniu kreator zapyta o SDK — zaakceptuj domyślne
     (zainstaluje „Android SDK Platform 35" lub podobne; jeśli spyta o ndk — odmów, niepotrzebne).
2. **Nie musisz** zakładać konta Google/developer, ani niczego płacić. Android Studio
   zapyta o zgodę na wysyłanie statystyk — bez znaczenia, co wybierzesz.

## Część B — build APK (~10 min)

1. Otwórz Android Studio → **File → Open** → wskaż folder `hal-widget/android`
   (ten, w którym leży `settings.gradle.kts`).
2. Poczekaj na zindeksowanie projektu (pasek na dole). Przy pierwszym otwarciu Gradle
   pobierze zależności — kilka minut, jednorazowo.
   - Jeśli na dole pojawi się błąd „Gradle sync failed" — **zrób zrzut ekranu i wyślij do mnie**,
     naprawię. To najbardziej prawdopodobne miejsce pierwszej poprawki.
3. Menu **Build → Build App Bundle(s) / APK(s) → Build APK(s)**.
4. Po zakończeniu: link „locate" w powiadomieniu w prawym dolnym rogu otworzy folder
   z plikiem **`app-debug.apk`**. To gotowa aplikacja do instalacji.

## Część C — instalacja na telefonie (~5 min)

1. Prześlij `app-debug.apk` na telefon (np. Google Drive, kabel, k synergy — cokolwiek).
2. Na telefonie otwórz plik. Android zapyta o zgodę na „instalację z nieznanych źródeł"
   — zgódź (dotyczy tylko tej aplikacji).
3. Otwórz aplikację „Hal":
   - wklej **URL panelu** (dam Ci go, gdy postawię backend — na teraz zostaw puste),
   - kliknij **„Nadaj uprawnienie overlay"** → w ustawieniach systemowych włącz przełącznik
     dla aplikacji Hal → wróć,
   - kliknij **„Start okna"**.
4. Efekt: pływające okno 340×480 dp w prawym górnym rogu, przeciągalne palcem.
   Test baterii: zostaw na dobę, sprawdź „Ustawienia → Bateria → Hal" — oczekiwane ≤2%/dobę.

## Część D — co możesz mi dać, żebym robił więcej sam

| Dostęp | Co mi daje | Jak |
|---|---|---|
| **Konto GitHub + fine-grained Personal Access Token** (uprawnienia: Contents+Actions na jednym repo) | Sam wypycham kod i uruchamiam build w chmurze; Ty tylko pobierasz gotowy APK z zakładki Actions. Zero instalowania czegokolwiek na PC. | 1. github.com → zarejestruj konto (jeśli nie masz). 2. Settings → Developer settings → Personal access tokens → Fine-grained → nowy token, repo „hal-widget", uprawnienia Contents: RW, Actions: RW. 3. Token podaj przez `assistant credentials prompt` (nigdy w czacie). |
| **Dostęp do Twojego PC przez klienta asystenta** | Mogę sam uruchamiać build lokalnie na Twojej maszynie (Android Studio + wiersz poleceń). | Instalacja klienta asystenta na PC + nadanie uprawnienia `host_bash`. |
| Nic z powyższego | Robisz build ręcznie według części B (10 minut na zmianę) — w pełni wykonalne, tylko wolniej. | — |

Rekomendacja: **GitHub + token** — to najmniej wysiłku z Twojej strony i pełna automatyzacja po mojej stronie.

## Znane ograniczenia etapu 1

- Panel treści nie ma jeszcze URL-a — dam znać, gdy postawię backend.
- Okno nie ma przycisku zamykania (zamykanie: aplikacja Hal → „Stop okna") ani zmiany rozmiaru
  gestem — dołożę w pierwszej iteracji po Twoich uwagach z prawdziwego użycia.
- Kod jeszcze nie przeszedł kompilacji — pierwszy build może wymagać mojej poprawki.
