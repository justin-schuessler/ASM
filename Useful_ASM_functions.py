import sys
import json
import datetime
import requests
from requests.auth import HTTPBasicAuth
import subprocess
import get_1password_field

Base_URL = "https://platform.sedaraapis.com/"
asm_out_path = "C:/Users/justin.schuessler/Documents/API_Output/Sedara_ASM/"


def list_asm_integrations(headers, tenant_id, params=None):
    if params is None:
        params = {"page": 1, "limit": 100, "pretty": "true", "include_health_report": "true", "include_configuration_report": "true", "include_disabled": "true"}

    response = requests.get(f"{Base_URL}" + "collector/v1/" + tenant_id + "/integrations", headers=headers, params=params)
    print(response.status_code)
    print(response.headers)
    # print(response.text)
    response.raise_for_status()
    return response.json()


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
    print(response.status_code)
    print(response.headers)
    # print(response.text)
    response.raise_for_status()

    return response.json()


def display_tenants(headers, params=None):
    tenants_return = list_asm_tenants(headers, params)
    tenants_list = tenants_return.get("tenants")
    for t in tenants_list:
        print(f"Name:{t['attributes'].get('name')}  |Hidden: {t['attributes'].get('hidden')}  |Type: {t['attributes'].get('type')}  |Kind: {t.get('kind')}  |ID: {t.get('id')} ")
    return tenants_list


def get_active_tenants(headers, params=None):
    tenants_return = list_asm_tenants(headers, params)
    tenants_list = tenants_return.get("tenants")
    active_tenants = {}
    for t in tenants_list:
        if not (t['attributes'].get('hidden')) and t['attributes'].get('type') == "CUSTOMER" and t.get('kind') == "platform_TENANT":
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


def get_base_url():
    return Base_URL


def get_asm_out_path():
    return asm_out_path


def get_asm_platform_api_access_key():
    return get_1password_field.get_1password_field("Sedara Platform ASM API", "Access key", "API")
