# Geo Explorer

A calm, no-timer geography game for the browser, in English and Italian. It's inspired by the old
Facebook game *Geo Challenge*, but made for learning rather than racing the clock.

**Play it:** https://annacuomo.github.io/geo-explorer/

## The games

- **Today's world tour**: ten mixed questions, the same for everyone each day.
- **Flags**: pick the right flag among six, or name the flag. 232 flags, territories included.
- **Capitals**: match each of 195 countries to its capital, either way round.
- **Shapes**: recognise 174 countries from their outline.
- **Cities**: click on the map as close as you can to 275 cities.
- **Landmarks**: coming soon.

Every game can be played as five levels that get gradually harder, or as "every one until you
know them all": anything you get wrong comes back at the end. Progress, stamps (one per region
per game) and the passport are saved in your browser. There is also a flag of the day and a
spinning globe that turns dark green as you learn countries.

## Running it

It's a single file. Open `index.html` in a browser, or serve the folder with any static server.
GitHub Pages serves it straight from this repository.

## Changing it

- **The game itself** (screens, rules, wording, colours) lives in `src/template.html`.
  After editing it, rebuild with:

  ```bash
  python3 scripts/build_page.py
  ```

- **The data** (names, capitals, difficulty tiers, Italian translations, which cities are in)
  lives in the plain-text files in `data/`. To regenerate the JSON from them:

  ```bash
  ./scripts/fetch_sources.sh            # downloads the open datasets into vendor/
  pip install numpy pillow playwright && playwright install chromium
  cd scripts
  python3 build_flags.py                # data/flags.json  (needs a headless browser)
  python3 build_shapes.py               # data/shapes.json
  python3 build_world.py                # data/world.json
  python3 build_cities.py               # data/cities.json
  python3 build_page.py                 # index.html
  ```

[HOW_IT_WORKS.md](HOW_IT_WORKS.md) explains how everything fits together.

## Credits and licences

The game's code is MIT licensed (see [LICENSE](LICENSE)). It is built on open data:

- Flags from [flag-icons](https://github.com/lipis/flag-icons) (MIT).
- Country outlines from [mledoze/countries](https://github.com/mledoze/countries) (ODbL),
  based on [Natural Earth](https://www.naturalearthdata.com).
- City locations from Natural Earth populated places (public domain).
- Fonts from Google Fonts: Fredoka, Bricolage Grotesque, Atkinson Hyperlegible (SIL Open Font License).

Built with help from Claude.
