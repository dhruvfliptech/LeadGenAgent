"""
Generate backend/app/data/locations_full.json by parsing craigslist.org/about/sites.

This script fetches the official Craigslist locations page and converts it
into the hierarchical JSON structure expected by the /api/v1/locations/import_full
endpoint. It builds:

- Group: "U.S. Locations" → states → cities
- Group: "World Locations" → regions (Africa, Americas, Asia / Pacific / Middle East, Europe, Oceania, Canada)
  - Canada → country("Canada") → provinces (states) → cities
  - Other regions → countries → cities

Run:
  python backend/scripts/generate_locations_full.py
"""

from __future__ import annotations

import json
import os
import sys
from typing import Dict, List, Tuple

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


CRAIGSLIST_SITES_URL = "https://www.craigslist.org/about/sites"


def _get_html(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


def _extract_section_blocks(soup: BeautifulSoup, anchor_name: str) -> List[Tuple[str, List[Tuple[str, str]]]]:
    """
    Return a list of (section_title, [(label, href), ...]) for a given top-level anchor section.

    The page structure is:
      <h2><a name="US"></a>US</h2>
      <div class="colmask">
        <div class="box ...">
          <h4>State or Country</h4>
          <ul>
            <li><a href="...">city label</a></li>
            ...
          </ul>
          (repeated)
        </div>
        (repeated boxes)
      </div>
    """
    anchor = soup.find("a", attrs={"name": anchor_name})
    if not anchor:
        return []

    h2 = anchor.parent if anchor.parent and anchor.parent.name == "h2" else None
    if not h2:
        return []

    # collect blocks until next h2
    blocks: List[Tuple[str, List[Tuple[str, str]]]] = []
    node = h2
    while True:
        node = node.find_next_sibling()
        if node is None:
            break
        if node.name == "h2":
            break
        # scan all h4/ul pairs under this node
        for h4 in node.find_all("h4"):
            title = h4.get_text(strip=True)
            ul = h4.find_next_sibling("ul")
            if not ul:
                continue
            items: List[Tuple[str, str]] = []
            for li in ul.find_all("li"):
                a = li.find("a")
                if not a or not a.get("href"):
                    continue
                label = a.get_text(strip=True)
                href = a["href"].strip()
                items.append((label, href))
            if items:
                blocks.append((title, items))
    return blocks


def _hostname_to_code(url: str) -> str:
    host = urlparse(url).netloc
    # e.g., sfbay.craigslist.org -> sfbay
    return host.split(".")[0]


def build_nodes() -> Dict[str, List[Dict]]:
    html = _get_html(CRAIGSLIST_SITES_URL)
    soup = BeautifulSoup(html, "html.parser")

    # US
    us_blocks = _extract_section_blocks(soup, "US")
    us_nodes: List[Dict] = []
    for state_name, cities in us_blocks:
        city_nodes = [
            {
                "type": "city",
                "label": label,
                "code": _hostname_to_code(href),
                "url": href,
                "state": state_name,
                "country": "US",
                "region": "US",
            }
            for label, href in cities
        ]
        us_nodes.append({"type": "state", "label": state_name, "children": city_nodes})
    us_nodes.sort(key=lambda s: s["label"])  # alphabetical states

    # World regions
    world_children: List[Dict] = []

    # Canada has provinces under its own anchor; we model it as a region with a single country
    ca_blocks = _extract_section_blocks(soup, "CA")
    if ca_blocks:
        provinces = []
        for prov_name, cities in ca_blocks:
            prov_cities = [
                {
                    "type": "city",
                    "label": label,
                    "code": _hostname_to_code(href),
                    "url": href,
                    "state": prov_name,
                    "country": "CA",
                    "region": "Canada",
                }
                for label, href in cities
            ]
            provinces.append({"type": "state", "label": prov_name, "children": prov_cities})
        provinces.sort(key=lambda s: s["label"])  # alphabetical provinces
        world_children.append(
            {
                "type": "region",
                "label": "Canada",
                "children": [
                    {"type": "country", "label": "Canada", "children": provinces}
                ],
            }
        )

    # Mapping of other anchors to region labels
    region_map = {
        "EU": "Europe",
        "ASIA": "Asia / Pacific / Middle East",
        "OCEANIA": "Oceania",
        "LATAM": "Americas",
        "AF": "Africa",
    }

    for anchor, region_label in region_map.items():
        blocks = _extract_section_blocks(soup, anchor)
        if not blocks:
            continue
        country_nodes: List[Dict] = []
        for country_name, cities in blocks:
            # Custom placement: treat "Guam / Micronesia" as part of Oceania in our hierarchy
            region_for_country = region_label
            if anchor == "ASIA" and "guam" in country_name.lower():
                region_for_country = "Oceania"
            city_nodes = [
                {
                    "type": "city",
                    "label": label,
                    "code": _hostname_to_code(href),
                    "url": href,
                    "state": None,
                    "country": country_name,
                    "region": region_for_country,
                }
                for label, href in cities
            ]
            # Some sections (e.g., Oceania) may list states within Australia; that's okay to keep flat.
            country_nodes.append({"type": "country", "label": country_name, "children": city_nodes})
        world_children.append({"type": "region", "label": region_label, "children": country_nodes})

    payload = {
        "nodes": [
            {"type": "group", "label": "U.S. Locations", "children": us_nodes},
            {"type": "group", "label": "World Locations", "children": world_children},
        ]
    }
    return payload


def write_payload(payload: Dict):
    # Resolve path: this script is at backend/scripts/, we want backend/app/data/locations_full.json
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.normpath(os.path.join(script_dir, "..", "app", "data", "locations_full.json"))
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    print(f"Wrote {data_path}")


def main() -> int:
    payload = build_nodes()
    write_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


