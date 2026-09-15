# Home Assistant integratie: reisdag-aggregator (uurlijkse reistijdvoorspelling)

## Context

Bestaande HA-integraties voor reistijd (`google_travel_time`, `waze_travel_time`) laten alleen de
*huidige* reistijd zien, live gepolld elke 5-10 minuten. Geen enkele bestaande integratie geeft een
vooruitblik: "als ik om 14:00 vertrek, hoe lang duurt het dan?" — terwijl providers als TomTom,
HERE en Google dat via een `departAt`/`departureTime`-parameter met verkeersvoorspelling wél
ondersteunen. Dit vult dat gat: een custom HA-integratie die voor een zelf ingesteld begin- en
eindpunt per uur een reistijdvoorspelling toont, zodat je in één oogopslag ziet wanneer je het beste
kunt vertrekken.

Doelgebruiker: jijzelf, op je eigen Home Assistant OS-installatie (Pi/mini-pc/NAS). Distributie
later via HACS als custom repository (zelfde aanpak als eerder met FormatSQL/FileTools besproken;
geen HA-core review nodig om te starten).

## Gekozen aanpak (uit overleg)

- **Databron: TomTom Routing API** — gratis tier van 2.500 non-tile requests/dag, géén creditcard
  nodig, en ondersteunt voorspelde reistijd op basis van historisch verkeer voor een opgegeven
  toekomstig tijdstip (`departAt`). Dit was de doorslaggevende reden boven HERE (30k/maand gratis,
  maar wél betaalmethode verplicht) en Google Routes API (creditcard verplicht, en traffic-aware
  calls vallen in het duurdere tarief, ~13k gratis calls/maand i.p.v. 40k).
- **Reismodus v1: alleen auto.** Verkeersvoorspelling heeft daar de meeste waarde; fiets/lopen/OV
  hebben geen zinvolle uur-tot-uur variatie in deze providers en zijn dus bewust uitgesteld.
- **Horizon: 48 uur vooruit, per uur** → 48 datapunten per route per refresh.
- **Call-budget:** bij het voorgestelde default refresh-interval van **2 uur** = 12 refreshes/dag ×
  48 calls = **576 calls/dag per route**, ruim binnen de 2.500/dag gratis limiet (marge voor ~4
  routes tegelijk op dit interval). Refresh-interval wordt instelbaar per route in de options flow,
  zodat je dit zelf kunt bijstellen als je meer routes toevoegt.
- **Testomgeving:** je draait al Home Assistant OS op eigen hardware. Deployment van de
  custom_component gaat via de Samba- of SSH & Terminal-add-on naar `/config/custom_components/`,
  gevolgd door een herstart van HA (exacte weg bepalen we bij implementatie, afhankelijk van welke
  add-on je al geïnstalleerd hebt).

## Architectuur

Standaard HA custom-integratie layout onder `custom_components/travel_forecast/`:

- **`manifest.json`** — `domain: travel_forecast`, `config_flow: true`, geen extra dependencies
  nodig (HA heeft `aiohttp` al ingebouwd).
- **`const.py`** — `DOMAIN`, config-keys (`CONF_NAME`, `CONF_ORIGIN`, `CONF_DESTINATION`,
  `CONF_API_KEY`, `CONF_REFRESH_INTERVAL`), vaste `HORIZON_HOURS = 48`.
- **`config_flow.py`** — één config entry per route: naam, origin (adres of `lat,lon`), destination,
  TomTom API-key, refresh-interval (default 2 uur, aanpasbaar via options flow). Adres wordt
  gegeocodeerd via TomTom's Search API als het geen `lat,lon` is.
- **`coordinator.py`** — `TravelForecastDataUpdateCoordinator(DataUpdateCoordinator)`: bouwt bij elke
  refresh 48 toekomstige uur-tijdstempels (gestart op het eerstvolgende hele uur), roept per
  tijdstip `TomTom /routing/1/calculateRoute` aan met `departAt` + `traffic=true`
  (`asyncio.gather` met een kleine concurrency-limiet om niet in één klap te bursten), en bewaart een
  lijst van `{timestamp, duration_min, distance_km}`.
- **`sensor.py`** — twee entiteiten per route:
  - **Hoofdsensor**: state = voorspelde reistijd (min) voor het eerstvolgende uur; attribuut
    `forecast` = volledige 48-punts lijst, plus `origin`, `destination`, `updated_at`.
  - **`best_departure`-sensor**: attributen `best_time` / `best_duration_min` — het gunstigste
    vertrekmoment binnen de 48 uur. Direct bruikbaar als "wanneer kan ik het beste vertrekken"-signaal,
    zonder dat je zelf door de forecast-lijst hoeft te bladeren.
- **`strings.json`/`translations/{en,nl}.json`** — labels voor de config flow.

## Visualisatie

Geen eigen Lovelace-kaart bouwen voor v1 — de `forecast`-attribuut-lijst is direct te plotten met de
populaire community **ApexCharts Card** (via HACS), die array-attributen al ondersteunt als
lijngrafiek.

## Buiten scope voor v1

- Andere reismodi dan auto (fiets/lopen/OV) — apart vervolg indien gewenst.
- Historische logging/statistiek buiten wat HA's recorder al automatisch doet voor sensoren.
- HA-core-opname — v1 wordt gedistribueerd als HACS custom repository.

## Implementatiestappen

1. Gratis TomTom API-key aanmaken (developer.tomtom.com, geen creditcard).
2. Los testscriptje (buiten HA) dat één `calculateRoute`-call met `departAt` doet tegen een echte
   route van jou (bijv. huis → werk of huis → judolocatie), om de vorm van request/response en
   eventuele rate-limit-headers te bevestigen vóórdat dit in de coordinator verwerkt wordt.
3. `custom_components/travel_forecast/` opbouwen zoals hierboven beschreven.
4. Lokaal in een losse map met `pytest-homeassistant-custom-component` de config_flow en coordinator
   testen (standaard testpatroon voor HA custom integraties) vóór deploy naar de echte HAOS-machine.
5. Deployen naar jouw HAOS via Samba/SSH-add-on, HA herstarten, route toevoegen via de UI
   (Instellingen → Apparaten & diensten → Integratie toevoegen).
6. Verificatie: sensor en `best_departure`-sensor moeten realistische, van elkaar verschillende
   waarden tonen over de 48 uur (bijv. duidelijk hogere reistijd tijdens spits dan 's nachts) —
   dat is het teken dat de traffic-aware voorspelling daadwerkelijk werkt en niet steeds dezelfde
   statische afstand/tijd teruggeeft.
7. Na een paar dagen echt gebruik: publiceren als HACS custom repository (nieuw GitHub-repo onder
   dm-utils, zelfde patroon als eerder gevolgd).
