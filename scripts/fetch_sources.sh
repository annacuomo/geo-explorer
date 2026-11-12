#!/usr/bin/env bash
# Downloads the open datasets the build scripts read, into ./vendor (not committed).
# You only need this to regenerate the files in data/; the game itself is built from data/.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p vendor
cd vendor

# Flag SVGs (MIT): https://github.com/lipis/flag-icons
[ -d flag-icons ] || git clone --depth 1 https://github.com/lipis/flag-icons

# Country outlines and metadata (ODbL): https://github.com/mledoze/countries
[ -d countries ] || git clone --depth 1 https://github.com/mledoze/countries

# Natural Earth populated places (public domain): https://github.com/nvkelso/natural-earth-vector
# The repository is very large, so only the one file we need is checked out.
if [ ! -d natural-earth-vector ]; then
  git clone --depth 1 --filter=blob:none --sparse https://github.com/nvkelso/natural-earth-vector
  git -C natural-earth-vector sparse-checkout set --no-cone /geojson/ne_50m_populated_places.geojson
fi
echo "Sources ready in vendor/"
