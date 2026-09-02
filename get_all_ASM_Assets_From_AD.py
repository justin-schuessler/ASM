"""Fetch every page from the Sedara ASM assets endpoint."""

from __future__ import annotations
from pathlib import Path
from typing import Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sys
import json
import datetime
import requests
from requests.auth import HTTPBasicAuth
import subprocess
import get_1password_field
from export_ou_structure import export_ou_structure


def get_all_assets(
    base_url: str,
    tenant_id: str,
    headers: dict[str, str],
    kind: str,
    *,
    limit: int = 1000,
    timeout: float = 60.0,
) -> list[dict[str, Any]]:
    """Request all asset pages and return one combined asset list."""
    if limit < 1:
        raise ValueError("limit must be at least 1")

    retry_policy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"POST"}),
        respect_retry_after_header=True,
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry_policy))

    url = f"{base_url.rstrip('/')}/{tenant_id}/assets"
    all_assets: list[dict[str, Any]] = []
    page = 1

    while True:
        payload = {"fql": kind, "page": page, "limit": limit}
        response = session.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()

        page_assets = result.get("assets")
        if not isinstance(page_assets, list):
            raise ValueError("API response does not contain an 'assets' list")

        all_assets.extend(page_assets)
        total = result.get("total")
        print(f"Fetched page {page}: {len(page_assets)} assets ({len(all_assets)} total)")

        # Stop when the server reports that all records were collected.
        if isinstance(total, int) and total > 0 and len(all_assets) >= total:
            break

        # A partial or empty page means there cannot be another full page.
        if len(page_assets) < limit:
            break

        page += 1

    return all_assets


def save_assets(assets: list[dict[str, Any]], output_path: str | Path) -> None:
    """Write the combined asset list to a formatted JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(assets, indent=2), encoding="utf-8")


if __name__ == "__main__":
    path = "C:/Users/justin.schuessler/Documents/API_Output/Sedara_ASM/"
    BASE_URL = "https://platform.sedaraapis.com/asm/"

    # Usage:
    #   python get_all_ASM_Assets_From_AD.py
    #   python get_all_ASM_Assets_From_AD.py --assets saved_assets.json
    #   python get_all_ASM_Assets_From_AD.py saved_assets.json
    arguments = sys.argv[1:]
    if arguments[:1] == ["--assets"]:
        if len(arguments) != 2:
            raise SystemExit(
                "Usage: python get_all_ASM_Assets_From_AD.py --assets JSON_FILE"
            )
        arguments = arguments[1:]
    elif len(arguments) > 1:
        raise SystemExit(
            "Usage: python get_all_ASM_Assets_From_AD.py [--assets JSON_FILE]"
        )

    loaded_from_file = bool(arguments)
    if loaded_from_file:
        assets_path = Path(arguments[0])
        with assets_path.open(encoding="utf-8-sig") as source:
            saved_data = json.load(source)

        if isinstance(saved_data, list):
            assets = saved_data
        elif isinstance(saved_data, dict):
            assets = saved_data.get("assets", saved_data.get("data"))
        else:
            assets = None

        if not isinstance(assets, list):
            raise ValueError(
                "Saved JSON must be an asset list or contain an 'assets' list"
            )
        print(f"Loaded {len(assets)} assets from {assets_path}")
    else:
        # tenant_id = get_1password_field.get_1password_field("Sedara Platform ASM API", "sedara tenant id", "API")

        # west herr
        tenant_id = "ca25595c-c6f0-4c58-9e9b-c83325eb9cc6"
        access_key = get_1password_field.get_1password_field("Sedara Platform ASM API", "Access key", "API")
        headers = {"Authorization":  f"Bearer {access_key}", "Content-Type": "application/json"}
        kind = '(class:Active-Directory-Computer OR class:Active-Directory-Group OR class:Active-Directory-User)include_stale:true include_hidden:true include_missing:true include_suppressed_by_age:true include_deleted:true'
        assets = get_all_assets(BASE_URL, tenant_id, headers, kind)

    fullpath_ou_json = path + "ASM_West_Herr_OU_Structure_v2.json"
    fullpath_ou_csv = path + "ASM_West_Herr_OU_Structure_v2.csv"
    tree, rows = export_ou_structure(
            assets,
            json_output_path=fullpath_ou_json,
            csv_output_path=fullpath_ou_csv,
        )

    if not loaded_from_file:
        Fullpath_assets = path + "ASM_west_herr_AD_all_Classes_1.json"
        save_assets(assets, Fullpath_assets)
        print(f"Saved {len(assets)}  ", Fullpath_assets)
