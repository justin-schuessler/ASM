"""Build an Active Directory OU hierarchy from Sedara ASM asset JSON."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any, Iterable


AD_RECORD_PATHS = {
    "User": ("user", "active_directory_user"),
    "Group": ("group", "active_directory_group"),
    "Device": ("device", "active_directory_computer"),
}


def _get_asset_list(document):
    if isinstance(document, list):
        assets = document
    elif isinstance(document, dict):
        assets = document.get("assets", document.get("data"))
    else:
        assets = None

    if not isinstance(assets, list):
        raise ValueError(
            "Input must be an asset list or a dictionary containing 'assets'"
        )

    return [asset for asset in assets if isinstance(asset, dict)]


def _split_distinguished_name(value: str) -> list[str]:
    """Split a DN on unescaped commas without requiring an LDAP package."""
    parts: list[str] = []
    current: list[str] = []
    escaped = False
    quoted = False

    for character in value:
        if escaped:
            current.append(character)
            escaped = False
        elif character == "\\":
            current.append(character)
            escaped = True
        elif character == '"':
            current.append(character)
            quoted = not quoted
        elif character == "," and not quoted:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(character)

    if current:
        parts.append("".join(current).strip())
    return parts


def _unescape_dn_value(value: str) -> str:
    """Decode common DN escapes, including hexadecimal byte escapes."""
    value = re.sub(
        r"\\([0-9A-Fa-f]{2})",
        lambda match: bytes.fromhex(match.group(1)).decode("utf-8", errors="replace"),
        value,
    )
    return re.sub(r"\\(.)", r"\1", value)


def _dn_components(distinguished_name: str) -> list[tuple[str, str]]:
    components: list[tuple[str, str]] = []
    for part in _split_distinguished_name(distinguished_name):
        key, separator, value = part.partition("=")
        if separator:
            components.append((key.strip().upper(), _unescape_dn_value(value.strip())))
    return components


def _get_ad_record(asset: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    outer_kind = str(asset.get("kind", ""))
    path = AD_RECORD_PATHS.get(outer_kind)
    if path is None:
        return None

    container = asset.get(path[0])
    if not isinstance(container, dict):
        return None
    record = container.get(path[1])
    if not isinstance(record, dict):
        return None

    asset_type = "Computer" if outer_kind == "Device" else outer_kind
    return asset_type, record


def _load_asset_list(input_path: str | Path) -> list[dict[str, Any]]:
    raw_text = Path(input_path).read_text(encoding="utf-8-sig")
    try:
        document = json.loads(raw_text)
    except json.JSONDecodeError:
        # Redacted exports may contain a blank property such as `"account": ,`.
        # Convert only blank object-property values to JSON null, then parse again.
        repaired_text = re.sub(
            r'(?m)^(\s*"(?:[^"\\]|\\.)+"\s*:\s*)(?=[,}])',
            r"\1null",
            raw_text,
        )
        # Also tolerate trailing commas introduced when fields were redacted.
        repaired_text = re.sub(r",(\s*[}\]])", r"\1", repaired_text)
        document = json.loads(repaired_text)

    if isinstance(document, list):
        assets = document
    elif isinstance(document, dict):
        assets = document.get("assets", document.get("data"))
    else:
        assets = None

    if not isinstance(assets, list):
        raise ValueError("Input JSON must be an asset list or contain an 'assets' list")
    return [asset for asset in assets if isinstance(asset, dict)]


def _new_ou(name: str, distinguished_name: str) -> dict[str, Any]:
    return {
        "name": name,
        "distinguished_name": distinguished_name,
        "organizational_units": [],
        "assets": [],
    }


def build_ou_structure(
    assets: Iterable[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return a nested OU tree and flat rows suitable for a CSV export."""
    domains: dict[str, dict[str, Any]] = {}
    flat_rows: list[dict[str, Any]] = []
    skipped = 0

    for asset in assets:
        located = _get_ad_record(asset)
        if located is None:
            skipped += 1
            continue

        asset_type, record = located
        distinguished_name = str(
            record.get("distinguished_name") or record.get("ou") or ""
        ).strip()
        if not distinguished_name:
            skipped += 1
            continue

        components = _dn_components(distinguished_name)
        domain_parts = [value for key, value in components if key == "DC"]
        # A DN lists the leaf OU first. Reverse it to construct root -> leaf.
        ou_names = [value for key, value in components if key == "OU"][::-1]
        cn_values = [value for key, value in components if key == "CN"]
        domain_name = ".".join(domain_parts) or "(unknown domain)"
        object_name = str(record.get("title") or record.get("name") or "")
        if cn_values:
            object_name = cn_values[0]

        domain_dn = ",".join(f"DC={part}" for part in domain_parts)
        domain_key = domain_name.casefold()
        domain = domains.setdefault(
            domain_key,
            {
                "name": domain_name,
                "distinguished_name": domain_dn,
                "organizational_units": [],
                "assets": [],
                "_ou_index": {},
            },
        )

        parent = domain
        accumulated_ous: list[str] = []
        for ou_name in ou_names:
            accumulated_ous.append(ou_name)
            path_key = "/".join(accumulated_ous)
            index = domain["_ou_index"]
            if path_key not in index:
                leaf_first = list(reversed(accumulated_ous))
                ou_dn = ",".join(
                    [*(f"OU={name}" for name in leaf_first), domain_dn]
                ).rstrip(",")
                node = _new_ou(ou_name, ou_dn)
                parent["organizational_units"].append(node)
                index[path_key] = node
            parent = index[path_key]

        asset_entry = {
            "name": object_name,
            "type": asset_type,
            "object_category": record.get("object_category", ""),
            "distinguished_name": distinguished_name,
        }
        parent["assets"].append(asset_entry)

        flat_rows.append(
            {
                "domain": domain["name"],
                "ou_path": "/".join(ou_names),
                "ou_depth": len(ou_names),
                "asset_type": asset_type,
                "asset_name": object_name,
                "object_category": record.get("object_category", ""),
                "distinguished_name": distinguished_name,
            }
        )

    def clean_and_sort(node: dict[str, Any]) -> None:
        node.pop("_ou_index", None)
        node["assets"].sort(key=lambda item: (item["type"], item["name"].casefold()))
        node["organizational_units"].sort(key=lambda item: item["name"].casefold())
        for child in node["organizational_units"]:
            clean_and_sort(child)

    domain_list = list(domains.values())
    domain_list.sort(key=lambda item: item["name"].casefold())
    for domain in domain_list:
        clean_and_sort(domain)
    flat_rows.sort(
        key=lambda row: (
            str(row["domain"]).casefold(),
            str(row["ou_path"]).casefold(),
            str(row["asset_type"]),
            str(row["asset_name"]).casefold(),
        )
    )

    tree = {
        "domains": domain_list,
        "summary": {
            "assets_exported": len(flat_rows),
            "assets_skipped": skipped,
        },
    }
    return tree, flat_rows


def build_hierarchy_csv_rows(
        asset_rows: Iterable[dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]]]:
    """Aggregate assets by path and format dynamic leaf-to-root columns."""
    aggregates: dict[tuple[str, ...], dict[str, Any]] = {}

    for asset in asset_rows:
        components = [
            value
            for key, value in _dn_components(str(asset["distinguished_name"]))
            if key in {"OU", "DC"}
        ]
        if not components:
            continue

        path_key = tuple(component.casefold() for component in components)
        aggregate = aggregates.setdefault(
            path_key,
            {
                "components": components,
                "computer_count": 0,
                "user_count": 0,
            },
        )
        if asset["asset_type"] == "Computer":
            aggregate["computer_count"] += 1
        elif asset["asset_type"] == "User":
            aggregate["user_count"] += 1

    maximum_depth = max(
        (len(item["components"]) for item in aggregates.values()), default=0
    )
    hierarchy_fields = [
        f"hierarchy_level_{level}"
        for level in range(maximum_depth, 0, -1)
    ]
    fieldnames = [*hierarchy_fields, "computer_count", "user_count"]
    csv_rows: list[dict[str, Any]] = []

    for aggregate in aggregates.values():
        components = aggregate["components"]
        padded_components = [""] * (maximum_depth - len(components)) + components
        row = dict(zip(hierarchy_fields, padded_components))
        row["computer_count"] = aggregate["computer_count"]
        row["user_count"] = aggregate["user_count"]
        csv_rows.append(row)

    csv_rows.sort(
        key=lambda row: tuple(
            str(row[field]).casefold() for field in reversed(hierarchy_fields)
        )
    )
    return fieldnames, csv_rows


def export_ou_structure(
        asset_data,
        json_output_path="ou_structure.json",
        csv_output_path="ou_structure.csv",
) -> tuple[dict, list]:
    """Read assets from JSON and write nested JSON plus flattened CSV outputs."""
    tree, asset_rows = build_ou_structure(_get_asset_list(asset_data))
    fieldnames, csv_rows = build_hierarchy_csv_rows(asset_rows)

    json_path = Path(json_output_path)
    csv_path = Path(csv_output_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with json_path.open("w", encoding="utf-8") as destination:
        json.dump(tree, destination, indent=2, ensure_ascii=False)

    with csv_path.open("w", encoding="utf-8-sig", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    return tree, csv_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="Sedara ASM asset JSON file")
    parser.add_argument("--json-output", default="ou_structure.json")
    parser.add_argument("--csv-output", default="ou_structure.csv")
    arguments = parser.parse_args()
    export_ou_structure(arguments.input, arguments.json_output, arguments.csv_output)


if __name__ == "__main__":
    main()
