import sys
import json
import datetime
import requests
from requests.auth import HTTPBasicAuth
import subprocess
import get_1password_field
import Useful_ASM_functions

if __name__ == "__main__":
    original_stdout = sys.stdout

    access_key = Useful_ASM_functions.get_asm_platform_api_access_key()
    headers = {"Authorization":  f"Bearer {access_key}",
               "Content-Type": "application/json"}

    active_tenants_list = Useful_ASM_functions.get_active_tenants(headers)
    all_integrations = {}
    for tenant_id in active_tenants_list.keys():
        customer_integrations = Useful_ASM_functions.get_active_integrations(headers=headers, tenant_id=tenant_id)
        all_integrations[tenant_id] = customer_integrations
        all_integrations[tenant_id]["name"] = active_tenants_list.get(tenant_id)

    data = all_integrations
    path = Useful_ASM_functions.get_asm_out_path()

    Fullpath = path + "ASM_all_integrations_all_tenants.json"
    f = open(Fullpath, "w")
    sys.stdout = f
    output = json.dumps(data, indent=4, )
    print(output)
    f.close()
    sys.stdout = original_stdout

