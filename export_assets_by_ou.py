"""Export assets from one or more OUs and enrich them with device details."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Iterable

#Example Usage
#python "export_assets_by_ou.py" `
#  --ou-structure "C:\Users\justin.schuessler\Documents\API_Output\Sedara_ASM\ASM_Taylor_Devices_OU_Structure_v2.json" `
#  --all-devices "C:\Users\justin.schuessler\Documents\API_Output\Sedara_ASM\ASM_AD_Taylor_Devices_All_Devices_1.json" `
#  --ous "Bitlocker,Servers" `
#  --output "C:\Users\justin.schuessler\Documents\API_Output\Sedara_ASM\Taylor_Selected_OU_Assets.txt"


OUTPUT_FIELDS = (
    "Asset Type",
    "Asset Name",
    "FQDN",
    "Private IP Address",
    "Operating System",
)


def load_json(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8-sig") as source:
        return json.load(source)


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _device_records(document: Any) -> list[dict[str, Any]]:
    if isinstance(document, list):
        records = document
    elif isinstance(document, dict):
        records = document.get("assets", document.get("data"))
    else:
        records = None

    if not isinstance(records, list):
        raise ValueError(
            "All-devices JSON must be a list or contain an 'assets' list"
        )
    return [record for record in records if isinstance(record, dict)]


def _device_name_keys(asset: dict[str, Any]) -> set[str]:
    device = asset.get("device")
    if not isinstance(device, dict):
        device = {}

    keys: set[str] = set()
    for source in (asset, device):
        for field in ("name", "title"):
            value = source.get(field)
            if value:
                keys.add(str(value).strip().casefold())
        for hostname in _as_string_list(source.get("hostnames")):
            keys.add(hostname.casefold())
            keys.add(hostname.split(".", 1)[0].casefold())

    ad_record = device.get("active_directory_computer")
    if isinstance(ad_record, dict):
        for field in ("name", "title", "sam_account_name"):
            value = ad_record.get(field)
            if value:
                keys.add(str(value).strip().rstrip("$").casefold())
        for hostname in _as_string_list(ad_record.get("hostnames")):
            keys.add(hostname.casefold())
            keys.add(hostname.split(".", 1)[0].casefold())
    return keys


def _device_details(asset: dict[str, Any]) -> dict[str, str]:
    device = asset.get("device")
    if not isinstance(device, dict):
        device = {}
    ad_record = device.get("active_directory_computer")
    if not isinstance(ad_record, dict):
        ad_record = {}

    hostnames = _as_string_list(device.get("hostnames"))
    if not hostnames:
        hostnames = _as_string_list(ad_record.get("hostnames"))
    fqdn = next((name for name in hostnames if "." in name), "")
    if not fqdn and hostnames:
        fqdn = hostnames[0]

    private_ips = _as_string_list(device.get("private_ip_addresses"))
    if not private_ips:
        private_ips = _as_string_list(ad_record.get("private_ip_addresses"))

    operating_system = (
        device.get("operating_system")
        or ad_record.get("operating_system")
        or ""
    )
    return {
        "FQDN": fqdn,
        "Private IP Address": "; ".join(dict.fromkeys(private_ips)),
        "Operating System": str(operating_system),
    }


def build_device_index(all_devices: Any) -> dict[str, dict[str, str]]:
    """Index device details by every useful name found in the API response."""
    index: dict[str, dict[str, str]] = {}
    for asset in _device_records(all_devices):
        details = _device_details(asset)
        for key in _device_name_keys(asset):
            index.setdefault(key, details)
    return index


def _walk_ous(nodes: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    for node in nodes:
        if not isinstance(node, dict):
            continue
        yield node
        children = node.get("organizational_units", [])
        if isinstance(children, list):
            yield from _walk_ous(children)


def _subtree_assets(node: dict[str, Any]) -> Iterable[dict[str, Any]]:
    assets = node.get("assets", [])
    if isinstance(assets, list):
        yield from (asset for asset in assets if isinstance(asset, dict))
    children = node.get("organizational_units", [])
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                yield from _subtree_assets(child)


def select_ou_assets(ou_structure: Any, ou_names: Iterable[str]) -> list[dict[str, Any]]:
    """Return unique assets in every named OU, including its descendant OUs."""
    if not isinstance(ou_structure, dict):
        raise ValueError("OU structure JSON must be an object")
    domains = ou_structure.get("domains")
    if not isinstance(domains, list):
        raise ValueError("OU structure JSON does not contain a 'domains' list")

    requested = {name.strip().casefold() for name in ou_names if name.strip()}
    if not requested:
        raise ValueError("At least one OU name is required")

    all_nodes: list[dict[str, Any]] = []
    for domain in domains:
        if isinstance(domain, dict):
            children = domain.get("organizational_units", [])
            if isinstance(children, list):
                all_nodes.extend(_walk_ous(children))

    matched_nodes = [
        node for node in all_nodes if str(node.get("name", "")).casefold() in requested
    ]
    found_names = {str(node.get("name", "")).casefold() for node in matched_nodes}
    missing = sorted(requested - found_names)
    if missing:
        available = sorted(
            {str(node.get("name", "")) for node in all_nodes if node.get("name")},
            key=str.casefold,
        )
        raise ValueError(
            f"OU(s) not found: {', '.join(missing)}. "
            f"Available OUs: {', '.join(available)}"
        )

    unique_assets: dict[tuple[str, str], dict[str, Any]] = {}
    for node in matched_nodes:
        for asset in _subtree_assets(node):
            asset_type = str(asset.get("type", ""))
            asset_name = str(asset.get("name", ""))
            key = (asset_type.casefold(), asset_name.casefold())
            unique_assets.setdefault(key, asset)
    return list(unique_assets.values())


def create_ou_asset_report(
    ou_structure: Any,
    all_devices: Any,
    ou_names: Iterable[str],
    output_path: str | Path,
) -> list[dict[str, str]]:
    """Create the quoted, comma-delimited TXT report and return its rows."""
    device_index = build_device_index(all_devices)
    selected_assets = select_ou_assets(ou_structure, ou_names)
    rows: list[dict[str, str]] = []

    for asset in selected_assets:
        asset_name = str(asset.get("name", ""))
        details = device_index.get(asset_name.casefold(), {})
        rows.append(
            {
                "Asset Type": str(asset.get("type", "")),
                "Asset Name": asset_name,
                "FQDN": details.get("FQDN", ""),
                "Private IP Address": details.get("Private IP Address", ""),
                "Operating System": details.get("Operating System", ""),
            }
        )

    rows.sort(key=lambda row: (row["Asset Type"].casefold(), row["Asset Name"].casefold()))
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=OUTPUT_FIELDS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export assets from selected OUs to a TXT report."
    )
    parser.add_argument("--ou-structure", required=True, help="OU structure JSON file")
    parser.add_argument("--all-devices", required=True, help="All-devices JSON file")
    parser.add_argument(
        "--ous",
        required=True,
        help='One or more comma-separated OU names, for example "Servers,Computers"',
    )
    parser.add_argument("--output", required=True, help="Output TXT filename")
    arguments = parser.parse_args()

    ou_names = [name.strip() for name in arguments.ous.split(",") if name.strip()]
    rows = create_ou_asset_report(
        load_json(arguments.ou_structure),
        load_json(arguments.all_devices),
        ou_names,
        arguments.output,
    )
    print(f"Saved {len(rows)} assets to {arguments.output}")


if __name__ == "__main__":
    main()
