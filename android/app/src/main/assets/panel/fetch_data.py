#!/usr/bin/env python3
"""
Hal Widget — zbieracz danych do panel.html (etap 3 zakresu surowcowego, 14.10).

Zakres surowcowy Barta (14.10): srebro USD/tr oz, miedź USD/lb, aluminium USD/lb,
stal HRC US Mid-west USD/lb. Aktualizacja godzinowa (harmonogram "Hal Widget —
dane panelu co godzinę").

Źródła:
  1. open-meteo  — pogoda dla Bielska-Białej (tło + temperatura)
  2. CoinGecko   — BTC / ETH (USD, PLN, zmiana 24h)
  3. Yahoo v8    — SI=F (USD/oz), HG=F (USD/lb), ALI=F (USD/t -> przelicz na lb)
  4. HRC US      — odczyt z dziennego raportu surowcowego
                   (/workspace/agenci/surowce/dane/historia.json, ostatni wpis);
                   TE blokuje nasz egress, a agent i tak mierzy HRC codziennie 08:00
  5. Frankfurter — USD/PLN, EUR

Zasada: każde źródło jest opcjonalne. Jeśli jedno padnie, panel dostaje
"stale": true przy tej sekcji i pokazuje ostatnią znaną wartość z cache.

Uwaga CORS (zmierzone 14.10): Yahoo i MetalCharts NIE wysyłają ACAO:*, więc
telefon nie pobierze surowców bezpośrednio — tylko z tego pliku. Pogoda,
krypto i kursy mają ACAO:* i panel pobiera je klientowo co godzinę; ten plik
jest dla nich fallbackiem offline. Aby surowce świeżyły się w telefonie
co godzinę bez przebudowy APK, ustaw w panelu ?src=<URL> na surowy plik
panel_data.json (np. raw.githubusercontent.com, tam CORS jest otwarty).

Użycie:  python3 fetch_data.py [--out panel_data.json]
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "panel_data.json")
HISTORIA = "/workspace/agenci/surowce/dane/historia.json"

UA = "Mozilla/5.0"  # prosty UA — dłuższe łapią 429 na query1.finance.yahoo.com
# mining.com z prostym UA zwraca błąd — tam potrzeba pełnego UA przeglądarki
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# Wiadomości (sekcja "news"): rynkowe + lokalne Bielsko-Biała (ustawione 14.10)
MARKET_FEEDS = [("Mining.com", "https://mining.com/feed/")]
LOCAL_FEEDS = [
    ("BB24", "https://bielsko-biala24.pl/feed"),
    ("BW", "https://bielsko-wiadomosci.pl/feed"),
]
ROADS_URL = "https://bielskiedrogi.pl/"  # parsowany HTML (brak RSS)

# Bielsko-Biała
LAT, LON = 49.8224, 19.0444

# sym, nazwa, jednostka, przelicznik z jednostki źródłowej na docelową
COMMODITIES = [
    ("SI=F", "Srebro", "USD/oz", 1.0),
    ("HG=F", "Miedź", "USD/lb", 1.0),
    ("ALI=F", "Aluminium", "USD/lb", 1.0 / 2204.62),  # Yahoo ALI=F jest w USD/t
]


def _get(url, timeout=25, attempts=3):
    last = None
    for a in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            time.sleep(1.5 + a * 2.5)
    raise last


def fetch_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&current=temperature_2m,apparent_temperature,weather_code,"
        "wind_speed_10m,relative_humidity_2m,is_day"
        "&daily=temperature_2m_max,temperature_2m_min,weather_code"
        "&timezone=Europe/Warsaw&forecast_days=3"
    )
    d = json.loads(_get(url))
    cur = d["current"]
    daily = d["daily"]
    return {
        "ok": True,
        "city": "Bielsko-Biała",
        "temp": cur["temperature_2m"],
        "feels": cur["apparent_temperature"],
        "code": cur["weather_code"],
        "wind": cur["wind_speed_10m"],
        "humidity": cur.get("relative_humidity_2m"),
        "is_day": bool(cur["is_day"]),
        "tmax": daily["temperature_2m_max"][0],
        "tmin": daily["temperature_2m_min"][0],
        "forecast": [
            {
                "date": daily["time"][i],
                "max": daily["temperature_2m_max"][i],
                "min": daily["temperature_2m_min"][i],
                "code": daily["weather_code"][i],
            }
            for i in range(len(daily["time"]))
        ],
        "observed": cur["time"],
    }


def fetch_crypto():
    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,ethereum&vs_currencies=usd,pln&include_24hr_change=true"
    )
    d = json.loads(_get(url))
    out = []
    for cid, label in (("bitcoin", "BTC"), ("ethereum", "ETH")):
        if cid in d:
            out.append(
                {
                    "sym": label,
                    "usd": d[cid]["usd"],
                    "pln": d[cid]["pln"],
                    "chg24": round(d[cid].get("usd_24h_change", 0.0), 2),
                }
            )
    return {"ok": True, "coins": out}


def _yahoo_quote(sym):
    """Ostatnia wycena + zmiana d/d na bazie dwóch OSTATNICH domknięć dziennych.
    W trakcie sesji ostatni bar jest formujący — d/d i tak liczymy względem
    przedostatniego zamknięcia, co jest zgodne ze słupkiem "wczoraj". """
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
    d = json.loads(_get(url))
    res = d["chart"]["result"][0]
    meta = res["meta"]
    closes = ((res.get("indicators") or {}).get("quote") or [{}])[0].get("quote_closes") or \
             ((res.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
    closes = [c for c in closes if c is not None]
    price = meta.get("regularMarketPrice")
    if price is None and closes:
        price = closes[-1]
    prev = closes[-2] if len(closes) >= 2 else None
    chg = round((price / prev - 1.0) * 100.0, 2) if (price and prev) else None
    ts = meta.get("regularMarketTime")
    as_of = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().strftime("%d.%m %H:%M") if ts else None
    return price, chg, as_of


def fetch_commodities():
    items = []
    updated = None
    for sym, name, unit, k in COMMODITIES:
        price, chg, as_of = _yahoo_quote(sym)
        if price is None:
            raise ValueError(f"{sym}: brak wyceny z Yahoo")
        items.append(
            {
                "sym": sym,
                "name": name,
                "unit": unit,
                "value": round(price * k, 4),
                "chg": chg,
                "as_of": as_of,
            }
        )
        if as_of:
            updated = max(updated, as_of) if updated else as_of

    # HRC US Mid-west — z dziennego raportu surowcowego (TE blokuje egress,
    # a agent surowcowy mierzy HRC codziennie rano; wartość jest datowana).
    hrc = _hrc_from_historia()
    if hrc:
        items.append(hrc)

    return {"ok": True, "items": items, "updated": updated}


def _hrc_from_historia():
    try:
        with open(HISTORIA, encoding="utf-8") as f:
            entries = json.load(f).get("entries", [])
        if not entries:
            return None
        last = entries[-1].get("hrc") or {}
        usd_t = last.get("us_usd_t")
        if not usd_t:
            return None
        prev_usd_t = None
        if len(entries) >= 2:
            prev_usd_t = (entries[-2].get("hrc") or {}).get("us_usd_t")
        chg = (
            round((usd_t / prev_usd_t - 1.0) * 100.0, 2)
            if prev_usd_t
            else None
        )
        us_date = last.get("us_date") or ""
        try:
            us_date = datetime.strptime(us_date, "%Y-%m-%d").strftime("%d.%m")
        except Exception:
            pass
        return {
            "sym": "HRC",
            "name": "Stal HRC US",
            "unit": "USD/lb",
            "value": round(usd_t / 2204.62, 4),
            "chg": chg,
            "as_of": us_date,
            "note": "pomiar dzienny 08:00",
        }
    except Exception:
        return None


def fetch_fx():
    d = json.loads(_get("https://api.frankfurter.dev/v1/latest?base=USD&symbols=PLN,EUR"))
    return {"ok": True, "date": d["date"], "usdpln": d["rates"]["PLN"], "usdeur": d["rates"]["EUR"]}


# ===================== wiadomości =====================

import re  # noqa: E402  (wyżej tylko stdlib-i, tu wygodniej mieć re przy newsach)


def _get_ua(url, ua, timeout=25, attempts=3):
    last = None
    for a in range(attempts):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            last = e
            time.sleep(1.5 + a * 2.5)
    raise last


def _strip_tags(s):
    import html as _html
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


# kategorie RSS = artykuły sponsorowane (BB24 oznacza je "Poradniki")
SPONSOR_CATS = ("poradnik", "sponsorowan", "materiał partnera", "partner")


def _parse_rss(xml, limit):
    out = []
    for m in re.finditer(r"<item[^>]*>(.*?)</item>", xml, re.S):
        it = m.group(1)
        title = re.search(r"<title>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", it, re.S)
        link = re.search(r"<link>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</link>", it, re.S)
        date = re.search(r"<pubDate>(.*?)</pubDate>", it, re.S)
        cats = " ".join(
            re.sub(r"<!\[CDATA\[|\]\]>", "", c).strip().lower()
            for c in re.findall(r"<category[^>]*>(.*?)</category>", it, re.S)
        )
        if not title:
            continue
        if any(s in cats for s in SPONSOR_CATS):
            continue
        out.append({
            "title": _strip_tags(title.group(1)),
            "url": link.group(1).strip() if link else "",
            "date": date.group(1).strip() if date else "",
        })
        if len(out) >= limit:
            break
    return out


def _parse_rss_date(s):
    """pubDate RFC822 -> epoch, albo None."""
    from email.utils import parsedate_to_datetime
    try:
        return parsedate_to_datetime(s).timestamp()
    except Exception:
        return 0


def _feed(url, ua=UA, limit=8):
    return _parse_rss(_get_ua(url, ua), limit)


def _roads(limit=6):
    html = _get_ua(ROADS_URL, BROWSER_UA)
    out = []
    for m in re.finditer(r"<article\b(.*?)</article>", html, re.S):
        art = m.group(1)
        t = re.search(r"<h3[^>]*>\s*<a[^>]*href=\"([^\"]+)\"[^>]*>(.*?)</a>", art, re.S)
        if not t:
            continue
        title = _strip_tags(t.group(2))
        if title.startswith("Materiał partnera"):
            continue
        tm = re.search(r"<time[^>]*datetime=\"([^\"]+)\"", art)
        out.append({
            "title": title,
            "url": t.group(1),
            "date": tm.group(1) if tm else "",
        })
        if len(out) >= limit:
            break
    return out


def fetch_news():
    """Rynkowe (mining.com; kitco nie ma już RSS, Bloomberg jest paywalowany —
    te dwa dochodzą na etapie biuletynu przez przeszukanie sieci)."""
    market = []
    for name, url in MARKET_FEEDS:
        try:
            for it in _feed(url, ua=BROWSER_UA, limit=8):
                it["src"] = name
                market.append(it)
        except Exception as e:
            sys.stderr.write(f"[warn] news {name}: {e}\n")
    market.sort(key=lambda x: _parse_rss_date(x.get("date", "")), reverse=True)

    local = []
    for name, url in LOCAL_FEEDS:
        try:
            for it in _feed(url, limit=6):
                it["src"] = name
                local.append(it)
        except Exception as e:
            sys.stderr.write(f"[warn] news {name}: {e}\n")
    local.sort(key=lambda x: _parse_rss_date(x.get("date", "")), reverse=True)

    try:
        roads = _roads()
    except Exception as e:
        sys.stderr.write(f"[warn] news drogi: {e}\n")
        roads = []

    if not (market or local or roads):
        raise ValueError("brak jakichkolwiek newsów")
    return {"ok": True, "market": market[:8], "local": local[:8], "roads": roads[:6]}


def load_cache():
    try:
        with open(CACHE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


SECTIONS = ("weather", "crypto", "commodities", "fx", "news")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=CACHE)
    args = ap.parse_args()

    prev = load_cache()
    data = {
        "generated": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }

    for key, fn in (
        ("weather", fetch_weather),
        ("crypto", fetch_crypto),
        ("commodities", fetch_commodities),
        ("fx", fetch_fx),
        ("news", fetch_news),
    ):
        try:
            data[key] = fn()
            data[key]["stale"] = False
        except Exception as e:
            sys.stderr.write(f"[warn] {key}: {e}\n")
            old = prev.get(key)
            if old:
                old = dict(old)
                old["stale"] = True
                data[key] = old
            else:
                data[key] = {"ok": False, "stale": True, "error": str(e)}

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    ok = [k for k in SECTIONS if data[k].get("ok")]
    stale = [k for k in SECTIONS if data[k].get("stale")]
    print(f"zapisano {args.out} | ok: {','.join(ok)} | stale: {','.join(stale) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
