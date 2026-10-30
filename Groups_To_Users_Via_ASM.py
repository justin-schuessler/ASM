import sys
import json
import datetime
import requests
from requests.auth import HTTPBasicAuth
import subprocess
import get_1password_field
import Useful_ASM_functions as USE


if __name__ == "__main__":
    tenant = "West Herr Automotive Group, Inc."
    business_tier_0_groups_path = "C:/Users/justin.schuessler/Documents/Sedara_ASM/Input_Static_Data/WH_business_tier_0_groups.json"
    access_key = USE.get_asm_platform_api_access_key()

    BASE_URL = "https://platform.sedaraapis.com/asm/"
    headers = {"Authorization":  f"Bearer {access_key}",
               "Content-Type": "application/json"}

    with open(business_tier_0_groups_path, "r", encoding="utf-8-sig") as b_file:
        tier_0_dict = json.load(b_file)
    groups_from_json = tier_0_dict.get("Business Tier-0 Groups")
    all_memebers = []
    tenant_id_list = USE.get_active_tenants(headers=headers)
    tenant_id = None
    for tenant_id_s in tenant_id_list:
        if tenant_id_list.get(tenant_id_s) == tenant:
            tenant_id = tenant_id_s
    if tenant_id is None:
        print("***FAILED TO IDENTIFY TENANT ID*** Exiting...")
        exit()

    #fql = 'kind:Group include_stale:true include_hidden:true include_missing:true include_suppressed_by_age:true include_deleted:true'
    #fql = 'kind:Group AND title:Billing and Title Clerks include_stale:true include_hidden:true include_missing:true include_suppressed_by_age:true include_deleted:true'
    #jsonz = {"fql": fql, "page": 1, "limit": 1000}
    filter_expr = "kind:Group AND title='{value}'"

    #response = requests.post(f"{BASE_URL}" + tenant_id + "/assets", headers=headers, json=jsonz)
    base = (f"{BASE_URL}" + tenant_id + "/assets")
    #All_Groups = USE.get_all_assets_from_fql(base, headers, jsonz)
    All_Groups = USE.aggregate_assets_from_values_list(values=groups_from_json, headers=headers, base_url=base, filter_expression=filter_expr,)
    print(len(All_Groups))

    for b_tier_0_g in All_Groups:
        classes = b_tier_0_g["group"].get("nested_classes")
        if classes is None:
            print(b_tier_0_g.get("title"))
        if classes is not None:
            for n_class in classes:
                if n_class == "Active-Directory-Group":
                    ad_keys_list = b_tier_0_g["group"]["active_directory_group"].get("members")
                    ad_filter_xpr = 'kind:User AND json("$.active_directory_user.distinguished_name") = {value}'
                    ad_users = USE.aggregate_assets_from_values_list(values=ad_keys_list, headers=headers, base_url=base, filter_expression=ad_filter_xpr)
                elif n_class == "Microsoft-Entra-Group":
                    en_dict_keys_list = b_tier_0_g["group"]["microsoft_entra_group"].get("members")
                    en_keys_list = []
                    for dict_key in en_dict_keys_list:
                        en_keys_list.append(dict_key.get("id"))
                    en_filter_xpr = 'kind:User AND json("$.microsoft_entra_user.id") = {value}'
                    ed_users = USE.aggregate_assets_from_values_list(values=en_keys_list, headers=headers, base_url=base, filter_expression=en_filter_xpr)
                else:
                    print(n_class)


    original_stdout = sys.stdout
    path = "C:/Users/justin.schuessler/Documents/API_Output/Sedara_ASM/"
    Fullpath = path + "ASM_WH_ALL_B_Tier_0_Groups_v_2.json"
    f = open(Fullpath, "w")
    sys.stdout = f
    output = json.dumps(All_Groups, indent=4, )
    print(output)
    f.close()
    sys.stdout = original_stdout

