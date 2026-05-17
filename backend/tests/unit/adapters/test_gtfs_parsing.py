"""Parse a tiny synthetic GTFS zip. Confirms the loader handles the real-world
shape we observed against the TUMI mirror without needing a network round trip.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from vambora.adapters.outbound.providers.gtfs_loader import (
    _parse_agencies,
    _parse_routes,
    _parse_stops,
    _read_csv,
    _read_feed_version,
)

pytestmark = pytest.mark.unit


_AGENCY = (
    "agency_id,agency_name,agency_url,agency_timezone,agency_lang\n"
    "22002,Intersul,http://www.rioonibus.com/,America/Sao_Paulo,pt\n"
)

_ROUTES = (
    "route_id,agency_id,route_short_name,route_long_name,route_desc,route_type,route_color,route_text_color,fare_id\n"
    'O0006AAA0A,22002,006,Silvestre - Castelo,"",700,FCC417,000000,""\n'
    'O0007AAA0A,22002,007,Silvestre - Central,"",700,FCC417,000000,""\n'
    "BAD,,,,,,,\n"
)

_STOPS = (
    "stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,zone_id,stop_url,location_type,parent_station,stop_timezone,wheelchair_boarding,platform_code\n"
    '1002O00010C0,"",AquaRio,"",-22.89331,-43.1926,"","",0,"","",,""\n'
    '1002O00013C0,"",Hospital dos Servidores,"",-22.89538,-43.18789,"","",0,"","",,""\n'
)

_FEED_INFO = (
    "feed_publisher_name,feed_publisher_url,feed_lang,feed_start_date,feed_end_date,feed_version,feed_contact_email\n"
    "SMTR,http://transportes.prefeitura.rio,pt,20240101,20241231,01Q0424,foo@example.com\n"
)


def _build_zip(tmp_path: Path) -> Path:
    p = tmp_path / "fixture.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("agency.txt", _AGENCY)
        z.writestr("routes.txt", _ROUTES)
        z.writestr("stops.txt", _STOPS)
        z.writestr("feed_info.txt", _FEED_INFO)
    return p


def test_parses_real_shaped_fixture(tmp_path: Path) -> None:
    archive = zipfile.ZipFile(_build_zip(tmp_path))

    agencies = list(_parse_agencies(_read_csv(archive, "agency.txt")))
    assert len(agencies) == 1
    assert agencies[0].name == "Intersul"

    routes = list(_parse_routes(_read_csv(archive, "routes.txt")))
    # The malformed BAD row is skipped by the parser's defensive guard.
    assert len(routes) == 2
    assert {r.short_name for r in routes} == {"006", "007"}
    assert routes[0].route_type == 700

    stops = list(_parse_stops(_read_csv(archive, "stops.txt")))
    assert len(stops) == 2
    assert stops[0].name == "AquaRio"
    assert stops[0].coordinate.latitude == pytest.approx(-22.89331)

    assert _read_feed_version(archive) == "01Q0424"


def test_parser_resilient_to_empty_optional_fields(tmp_path: Path) -> None:
    src = (
        "stop_id,stop_code,stop_name,stop_desc,stop_lat,stop_lon,zone_id,stop_url,location_type,parent_station,stop_timezone,wheelchair_boarding,platform_code\n"
        "X,,Some Stop,,0.0,0.0,,,0,,,,\n"
    )
    p = tmp_path / "edge.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("stops.txt", src)
    archive = zipfile.ZipFile(p)
    stops = list(_parse_stops(_read_csv(archive, "stops.txt")))
    assert len(stops) == 1
    assert stops[0].code is None
    assert stops[0].parent_station is None
    assert stops[0].wheelchair_boarding is None
