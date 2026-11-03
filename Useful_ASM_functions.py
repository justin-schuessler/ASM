import sys
import json
import datetime
import requests
import time
from requests.auth import HTTPBasicAuth
import subprocess
import get_1password_field
import os
from openpyxl import Workbook
from collections import Counter
from collections import defaultdict


Base_URL = "https://platform.sedaraapis.com/"
asm_out_path = "C:/Users/justin.schuessler/Documents/API_Output/Sedara_ASM/"
asm_report_path = "A:/Cyber_Operations/ASM_Reports/"


# changes nested classes string to dict key string
def clean_class(nested):
    clean = nested.lower().replace("-", "_")
    return clean


# changes _group at end of classes to _user
def group_to_user(value: str) -> str:
    return value[:-6] + "_user" if value.endswith("_group") else value


def list_asm_integrations(headers, tenant_id, params=None):
    if params is None:
        params = {"page": 1, "limit": 100, "pretty": "true", "include_health_report": "true",
                  "include_configuration_report": "true", "include_disabled": "true"}

    response = requests.get(f"{Base_URL}" + "collector/v1/" + tenant_id + "/integrations", headers=headers,
                            params=params)
    print(response.status_code)
    # print(response.headers)
    # print(response.text)
    response.raise_for_status()
    return response.json()


def get_active_integrations(headers, tenant_id, params=None):
    all_tenant_integrations = list_asm_integrations(headers=headers, tenant_id=tenant_id, params=params)
    tenant_integration_dict_list = all_tenant_integrations.get("data")
    configured_integrations_list = {}
    not_configured_integration_list = {}

    for integration in tenant_integration_dict_list:
        status_list = []
        state = False
        integration_out_dict = {}
        enabled = integration["attributes"].get("enabled")
        name = integration["attributes"].get("title")
        configured = integration["meta"].get("configured")
        description = integration["attributes"].get("description")
        integration_id = integration.get("id")
        integration_out_dict["name"] = name
        integration_out_dict["description"] = description
        if configured > 0:
            config_report = integration["meta"].get("configuration_reports")
            health_report = integration["meta"].get("health_report")

            try:
                recent_conf_report = config_report[0]
                conf_report_attributes = recent_conf_report.get("attributes")
                status_list = conf_report_attributes.get("status")

            except:
                print("Name:  ", name, "     Configured:  ", configured)
                print("Config Reports: ", config_report)
                print(tenant_id)

            try:
                health_report = integration["meta"].get("health_report")
                health_rep_attrib = health_report.get("attributes")
                state = health_rep_attrib.get("state")

            except:
                print("Name:  ", name, "     Configured:  ", configured)
                print("Health Reports: ", health_report)
                print(tenant_id)

            last_seen = integration["meta"].get("last_seen_at")
            healthy = False

            integration_out_dict["status_list"] = status_list
            integration_out_dict["state"] = state
            integration_out_dict["last_seen"] = last_seen

            for status in status_list:
                if status == "Healthy":
                    healthy = True

            if state and healthy:
                healthy = True

            integration_out_dict["healthy"] = healthy
            configured_integrations_list[integration_id] = integration_out_dict

        if configured == 0:
            not_configured_integration_list[integration_id] = integration_out_dict

    tenant_configuration_stats_dict = {}
    tenant_configuration_stats_dict["configured_integrations_list"] = configured_integrations_list
    tenant_configuration_stats_dict["not_configured_integration_list"] = not_configured_integration_list
    return tenant_configuration_stats_dict


# forbiden? receive "you probably should not be here" message
def list_asm_organizations(headers, params=None):
    if params is None:
        params = {"page": 1, "per_page": 100}

    response = requests.get(f"{Base_URL}" + "dataservices/v2/organizations", headers=headers, params=params)
    print(response.status_code)
    print(response.headers)
    print(response.text)
    response.raise_for_status()

    return response.json()


def list_asm_tenants(headers, params=None):
    if params is None:
        params = {"page": 1, "size": 300}

    response = requests.get(f"{Base_URL}" + "tenant-management/tenants", headers=headers, params=params)
    # print(response.status_code)
    # print(response.headers)
    # print(response.text)
    response.raise_for_status()

    return response.json()


def display_tenants(headers, params=None):
    tenants_return = list_asm_tenants(headers, params)
    tenants_list = tenants_return.get("tenants")
    for t in tenants_list:
        print(
            f"Name:{t['attributes'].get('name')}  |Hidden: {t['attributes'].get('hidden')}  |Type: {t['attributes'].get('type')}  |Kind: {t.get('kind')}  |ID: {t.get('id')} ")
    return tenants_list


def get_active_tenants(headers, params=None):
    tenants_return = list_asm_tenants(headers, params)
    tenants_list = tenants_return.get("tenants")
    active_tenants = {}
    for t in tenants_list:
        if not (t['attributes'].get('hidden')) and t['attributes'].get('type') == "CUSTOMER" and t.get(
                'kind') == "platform_TENANT":
            active_tenants[t.get('id')] = t['attributes'].get('name')

    return active_tenants


# Return Empty List Currently
def list_all_asm_collectors_health(headers, params=None):
    if params is None:
        params = {"pretty": "true"}

    response = requests.get(f"{Base_URL}" + "collector/v1/collectors/health", headers=headers, params=params)
    print(response.status_code)
    print(response.headers)
    # print(response.text)
    response.raise_for_status()

    return response.json()


def out_to_excel(data, xl_save_path):
    wb = Workbook()
    ws = wb.active
    row = 2

    ws["A1"] = "Tenant ID"
    ws["B1"] = "Tenant Name"
    ws["C1"] = "Integration Name"
    ws["D1"] = "Integration ID"
    ws["E1"] = "Healthy"
    ws["F1"] = "State"
    ws["G1"] = "Status List"
    ws["H1"] = "Last Seen"
    data_keys = data.keys()

    for key in data_keys:
        configed_dict = data[key].get("configured_integrations_list")
        if len(configed_dict) > 0:
            for configed_integration in data[key].get("configured_integrations_list").keys():
                ws.cell(row=row, column=1).value = key
                ws.cell(row=row, column=2).value = data[key].get("name")
                ws.cell(row=row, column=3).value = data[key]["configured_integrations_list"][configed_integration].get(
                    "name")
                ws.cell(row=row, column=4).value = configed_integration
                ws.cell(row=row, column=5).value = data[key]["configured_integrations_list"][configed_integration].get(
                    "healthy")
                ws.cell(row=row, column=6).value = data[key]["configured_integrations_list"][configed_integration].get(
                    "state")
                status_string = ", ".join(
                    data[key]["configured_integrations_list"][configed_integration].get("status_list"))
                ws.cell(row=row, column=7).value = status_string
                ws.cell(row=row, column=8).value = data[key]["configured_integrations_list"][configed_integration].get(
                    "last_seen")
                row += 1

    wb.save(xl_save_path)
    directory, filename = os.path.split(xl_save_path)
    print("File:  ", filename, "  Saved To Directory:  ", directory)


def get_base_url():
    return Base_URL


def get_asm_out_path():
    return asm_out_path


def get_asm_report_out_path():
    return asm_report_path


def get_asm_platform_api_access_key():
    return get_1password_field.get_1password_field("Sedara Platform ASM API", "Access key", "API")


def get_software_vuln_data(tenant, headers, params=None):
    if params is None:
        params = {"include_cves": "true"}

    response = requests.get(f"{Base_URL}" + f"asm/{tenant}/tech-stack", headers=headers, params=params)
    print(response.status_code)
    print(response.headers)
    # print(response.text)
    response.raise_for_status()

    return response.json()


def get_all_assets_from_fql(base: str, headers: dict[str, str],
                            jsonz: dict, timeout: float = 60, ) -> list[dict]:
    """Fetch and aggregate every page of assets."""
    """Used to Return a Large list of assets with multiple Pages"""
    payload = {**jsonz, "page": 0}
    limit = payload.setdefault("limit", 1000)

    if type(limit) is not int or limit <= 0:
        raise ValueError("'limit' must be a positive integer.")

    with requests.Session() as session:

        def fetch_page(page: int) -> dict:
            response = session.post(
                base,
                headers=headers,
                json={**payload, "page": page},
                timeout=timeout,
            )
            response.raise_for_status()
            # print(response.status_code)
            result = response.json()

            if not isinstance(result.get("data"), list):
                raise ValueError(f"Page {page}: expected an 'assets' list.")

            if result.get("page") != page:
                raise ValueError(
                    f"Requested page {page}, but API returned page "
                    f"{result.get('page')!r}."
                )
            return result

        first_page = fetch_page(1)
        total = first_page.get("total")
        print(
            f"Requested page={1}, "
            f"returned page={first_page.get('page')}, "
            f"present={first_page.get('present')}, "
            f"total={first_page.get('total')}, "
            f"received={len(first_page['data'])}"
        )

        if type(total) is not int or total < 0:
            raise ValueError("'total' must be a non-negative integer.")

        page_count = (total + limit - 1) // limit
        assets = list(first_page["data"])

        for page in range(2, page_count + 1):
            result = fetch_page(page)

            print(
                f"Requested page={page}, "
                f"returned page={result.get('page')}, "
                f"present={result.get('present')}, "
                f"total={result.get('total')}, "
                f"received={len(result['data'])}"
            )

            if result["data"] == first_page["data"]:
                raise ValueError(
                    f"Page {page} contains the same assets as page 0. "
                    "The API is repeating the first page."
                )

            assets.extend(result["data"])
    if len(assets) != total:
        raise ValueError(
            f"Expected {total} assets, but received {len(assets)}."
        )

    return assets


# Takes a list of values and fql expression and hits ASM API 1 at a time
# returns aggregated list of all queries for it against given endpoint
def aggregate_assets_from_values_list(values: list[str], headers: dict[str, str], base_url: str, filter_expression: str,
                                      evaluate_output: bool = True,
                                      includes: str = (
                                              "include_stale:true "
                                              "include_hidden:true "
                                              "include_missing:true "
                                              "include_suppressed_by_age:true "
                                              "include_deleted:true"
                                      ),
                                      limit: int = 100,
                                      timeout: float = 60,
                                      ) -> tuple[list[dict], list]:
    if "{value}" not in filter_expression:
        raise ValueError("filter_expression must contain '{value}'.")
    if type(limit) is not int or limit <= 0:
        raise ValueError("limit must be a positive integer.")
    # Remove duplicates while preserving input order.
    unique_values = list(dict.fromkeys(values))
    aggregated = []
    missing = []

    def fetch_page(fql: str, page: int) -> dict:
        max_attempts = 3
        for attempt in range(max_attempts):
            response = requests.post(base_url, headers=headers, json={"fql": fql, "page": page, "limit": limit})
            # print("JSON: \n", response.json())
            # print("TEXT: \n", response.text)
            # print("URL: \n", response.url)
            database_locked = (
                    response.status_code == 500
                    and "SQLITE_BUSY" in response.text
            )
            if database_locked and attempt < max_attempts - 1:
                delay = 2 ** (attempt + 1)
                print(
                    f"Database locked on page {page}. "
                    f"Retrying in {delay} seconds "
                    f"(attempt {attempt + 2}/{max_attempts})..."
                )
                time.sleep(delay)
                continue
            if not response.ok:
                raise requests.HTTPError(
                    f"HTTP {response.status_code}\n"
                    f"Filter: {fql}\n"
                    f"Response: {response.text[:2000]}",
                    response=response,
                )
            body = response.json()
            if not isinstance(body.get("data"), list):
                raise ValueError(
                    f"Page {page}: response must contain a 'data' list."
                )
            return body

    for value in unique_values:
        print(value)
        fql = (
            f"{filter_expression.replace('{value}', value)} "
            f"{includes}"
        ).strip()
        #print(fql)
        first_page = fetch_page(fql, 1)
        query_results = list(first_page["data"])
        if not query_results:
            missing.append(value)
            print(f"ERROR: No data returned for {value!r}")
            continue
        total = first_page.get("total")
        if type(total) is not int or total < 0:
            raise ValueError(
                f"{value!r}: response must contain a valid 'total'."
            )
        page_count = (total + limit - 1) // limit
        for page in range(2, page_count + 1):
            query_results.extend(fetch_page(fql, page)["data"])
        if len(query_results) != total:
            raise ValueError(
                f"{value!r}: expected {total} records, "
                f"received {len(query_results)}."
            )
        if len(query_results) > 1:
            print(
                f"WARNING: {value!r} returned "
                f"{len(query_results)} records; expected one."
            )
            for q in query_results:
                print("TITLE:  ", q.get("title"))
                print("UID:  ", q.get("uid"))
        aggregated.extend(query_results)
    input_titles = set(unique_values)
    output_counts = Counter(
        record.get("title")
        for record in aggregated
        if isinstance(record.get("title"), str)
    )
    print(
        f"Inputs: {len(values)} | "
        f"Unique inputs: {len(unique_values)} | "
        f"Output records: {len(aggregated)}"
    )
    if len(aggregated) != len(unique_values):
        print(
            "WARNING: Input/output count mismatch: "
            f"{len(unique_values)} unique inputs versus "
            f"{len(aggregated)} output records."
        )

    if evaluate_output:
        duplicates = {
            title: count
            for title, count in output_counts.items()
            if count > 1
        }
        unexpected = set(output_counts) - input_titles
        missing_titles = input_titles - set(output_counts)
        if duplicates:
            print("\nDuplicate output titles:")
            for title, count in sorted(duplicates.items()):
                print(f"  - {title!r}: {count} records ({count - 1} extra)")
        if unexpected:
            print("\nOutput titles not in the input list:")
            for title in sorted(unexpected):
                print(f"  - {title!r}: {output_counts[title]} records")
        if missing_titles:
            print("\nInput titles missing from the output:")
            for title in sorted(missing_titles):
                print(f"  - {title!r}")
        for index, record in enumerate(aggregated):
            if not isinstance(record.get("title"), str):
                print(
                    f"WARNING: Output record at index {index} "
                    f"has a missing or non-string title: {record!r}"
                )
    return aggregated, missing


# Input list of ASM Group dicts
# Outputs aggregated list of all members from each nested class found
def members_from_asm_groups(input_groups: list[dict]):
    master_dict_all_data = {"group_nested_classes": set(),
                            "user_nested_classes": set(),
                            "group_emails": {},
                            "group_members": [],
                            "groups_no_members": {}
                            }
    groups_classes = master_dict_all_data["group_nested_classes"]
    groups_members = master_dict_all_data["group_members"]
    groups_no_members = master_dict_all_data["groups_no_members"]
    member_counter = {}
    master_discrep = {}
    for grp in input_groups:
        g_title = grp.get("title")
        classes = grp["group"].get("nested_classes")
        if master_dict_all_data["group_emails"].get(g_title) is None:
            master_dict_all_data["group_emails"][g_title] = set()
        if classes is None:
            print("Group:  ", grp.get("title"), "  Has no classes")
        if classes is not None:
            for n_class in classes:
                if master_dict_all_data["group_emails"].get(g_title) is not None:
                    grp_c_em = grp["group"][clean_class(n_class)].get("email")
                    if grp_c_em is not None:
                        for g_em in grp_c_em:
                            master_dict_all_data["group_emails"][g_title].add(g_em)
                m_keys = grp["group"][clean_class(n_class)].get("members")
                if m_keys is not None:
                    if member_counter.get(g_title) is None:
                        member_counter[g_title] = {}
                    if member_counter.get(g_title) is not None:
                        member_counter[g_title][clean_class(n_class)] = len(m_keys)
                    groups_members.append(m_keys)
                if m_keys is None:
                    groups_no_members[g_title] = clean_class(n_class)
                groups_classes.add(n_class)
        if member_counter.get(g_title) is not None:
            if len(member_counter.get(g_title)) > 1:
                master_discrep[g_title] = find_class_discrepancies(member_counter.get(g_title))
    for n_g_c in master_dict_all_data.get("group_nested_classes"):
        n_u_c = group_to_user(clean_class(n_g_c))
        master_dict_all_data["user_nested_classes"].add(n_u_c)
    return master_dict_all_data, master_discrep


# Input data of following format
# data = {
#     "Group A": {"class_1": 7, "class_2": 8},
#     "Group B": {"class_1": 5, "class_2": 5},
# }
# Output (and print -option) discrepancies in class # values
def find_class_discrepancies(classes: dict[str, int], print_output: bool = True) -> dict:
    counts = Counter(classes.values())
    if len(counts) <= 1:
        return {}
    highest_frequency = max(counts.values())
    most_common = [
        value
        for value, frequency in counts.items()
        if frequency == highest_frequency
    ]
    if len(most_common) > 1:
        r = {"issue": "Class counts differ; no single most common count.",
            "classes": dict(classes)}
        if print_output:
            print("print r: ", r)
        return r

    expected = most_common[0]
    re = {
        "expected_count": expected,
        "flagged_classes": {
            name: value
            for name, value in classes.items()
            if value != expected
        },
    }
    if print_output:
        print("print re:", re)
    return re


# Inputs dirty list of mixed type of member records
# Outputs clean list of de-duplicated ASM User records
def clean_asm_group_members(members: list, users_master: dict, user_classes: list):
    all_users_uid: dict[str, list] = defaultdict(list)
    member_strings = []
    member_dicts = []
    member_dict_to_id = {}
    for m in members:
        if isinstance(m, list) and m:
            if all(isinstance(dict_m, dict) for dict_m in m):
                member_dicts.extend(m)
            elif all(isinstance(str_m, str) for str_m in m):
                member_strings.extend(m)
            else:
                print("Mixed types")

# turns Entra dicts into id for unique id
    for m_d in member_dicts:
        m_email = m_d.get("email")
        m_id = m_d.get("id")
        if m_id is not None:
            if m_email is not None:
                member_dict_to_id[m_id] = m_email
            if m_email is None:
                member_dict_to_id[m_id] = []
        else:
            print("Member has no id \n", m_id)

    dn_str_keys = dict.fromkeys(member_strings)
    print(f"Number of AD Users: {len(dn_str_keys)}")
    print(f"Number of Entra Users: {len(member_dict_to_id)}")
    for user in users_master:
        if user.get("user") is not None:
            popped = 0
            for u_class in user_classes:
                if user["user"].get(u_class) is not None:
                    if user["user"][u_class].get("distinguished_name") is not None:
                        if user["user"][u_class].get("distinguished_name") in dn_str_keys:
                            all_users_uid[user.get("uid")].append(user["user"][u_class].get("distinguished_name"))
                            dn_str_keys.pop(user["user"][u_class].get("distinguished_name"))
                            popped = popped + 1

                    if user["user"][u_class].get("id") is not None:
                        if user["user"][u_class].get("id") in member_dict_to_id:
                            all_users_uid[user.get("uid")].append(user["user"][u_class].get("id"))
                            member_dict_to_id.pop(user["user"][u_class].get("id"))
                            popped = popped + 1

                    if popped < 2:
                        if user["user"][u_class].get("on_premises_distinguished_name") is not None:
                            if user["user"][u_class].get("on_premises_distinguished_name") in dn_str_keys:
                                all_users_uid[user.get("uid")].append(user["user"][u_class].get("on_premises_distinguished_name"))
                                dn_str_keys.pop(user["user"][u_class].get("on_premises_distinguished_name"))
                                popped = popped + 1

                    if popped < 2:
                        u_p_n = user["user"][u_class].get("user_principal_name")
                        u_uc_emails = user["user"][u_class].get("email")
                        if u_p_n is not None:
                            for m_id in member_dict_to_id:
                                m_pop = 0
                                for mbr_dict_id_value_e in member_dict_to_id.get(m_id):
                                    if u_p_n == mbr_dict_id_value_e:
                                        all_users_uid[user.get("uid")].append(u_p_n)
                                        member_dict_to_id.pop(m_id)
                                        popped = popped + 1
                                        m_pop = m_pop + 1

                                if u_uc_emails is not None:
                                    for u_e in u_uc_emails:
                                        if u_e == member_dict_to_id.get(m_id):
                                            all_users_uid[user.get("uid")].append(u_p_n)
                                            member_dict_to_id.pop(m_id)
                                            popped = popped + 1
                                            m_pop = m_pop + 1
                                if m_pop > 0:
                                    break

    return all_users_uid, dn_str_keys, member_dict_to_id


