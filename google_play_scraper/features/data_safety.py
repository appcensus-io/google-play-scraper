import json

from google_play_scraper.constants.element import ElementSpecs
from google_play_scraper.constants.element import resolve_specs
from google_play_scraper.constants.regex import Regex
from google_play_scraper.constants.request import Formats
from google_play_scraper.utils.request import post
from google_play_scraper.exceptions import NotFoundError


def data_safety(app_id: str, lang: str = "en", country: str = "us") -> dict[str, list]:
    dom = post(
        Formats.DataSafety.build(lang=lang, country=country),
        Formats.DataSafety.build_body(app_id),
        {"content-type": "application/x-www-form-urlencoded;charset=UTF-8"},
    )

    return _parse_dom(dom)


def _parse_dom(dom: str) -> dict[str, list]:
    result: dict[str, list] = {}
    matches = json.loads(Regex.PERMISSIONS.findall(dom)[0])
    container_json = matches[0][2]

    if container_json is None:
        raise NotFoundError("App not found.")

    container = json.loads(container_json)

    return resolve_specs(container, ElementSpecs.DataSafety)
