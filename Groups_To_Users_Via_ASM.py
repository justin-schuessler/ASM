import sys
import json
import datetime
import requests
from requests.auth import HTTPBasicAuth
import subprocess
import get_1password_field
import Useful_ASM_functions as USE
from collections import defaultdict


def input_group_data():
    with open(business_tier_0_groups_path, "r", encoding="utf-8-sig") as b_file:
        tier_0_dict = json.load(b_file)
    groups_from_json = tier_0_dict.get("Business Tier-0 Groups")
    return groups_from_json


def input_user_data():
    with open(WH_users, "r", encoding="utf-8-sig") as u_file:
        users = json.load(u_file)
    return users


def input_all_groups():
    with open(all_gs, "r", encoding="utf-8-sig") as g_file:
        groups = json.load(g_file)
    return groups


if __name__ == "__main__":
    args = sys.argv
    if len(args) >= 2:
        directory = args[1]
        if directory == "network" or directory == "NETWORK":
            network_path = USE.get_asm_report_out_path()

    tenant = "West Herr Automotive Group, Inc."
    WH_users = "C:/Users/justin.schuessler/Documents/API_Output/Sedara_ASM/ASM_AD_WH_all_users.json"
    all_gs = "C:/Users/justin.schuessler/Documents/API_Output/Sedara_ASM/ASM_WH_ALL_Groups.json"
    business_tier_0_groups_path = "C:/Users/justin.schuessler/Documents/Sedara_ASM/Input_Static_Data/WH_business_tier_0_groups.json"
    #access_key = USE.get_asm_platform_api_access_key()

    BASE_URL = "https://platform.sedaraapis.com/asm/"
    #headers = {"Authorization":  f"Bearer {access_key}",
    #           "Content-Type": "application/json"}
    input_groups = input_group_data()
    input_groups_dict = dict.fromkeys(input_groups)
    input_groups_set = set(input_groups)
    #print("Input Groups Dict: \n", input_groups_dict)
    all_memebers = []
    #tenant_id_list = USE.get_active_tenants(headers=headers)
    #tenant_id = None
    #for tenant_id_s in tenant_id_list:
    #    if tenant_id_list.get(tenant_id_s) == tenant:
    #        tenant_id = tenant_id_s
    #if tenant_id is None:
    #    print("***FAILED TO IDENTIFY TENANT ID*** Exiting...")
    #    exit()

    fql = 'kind:Group include_stale:true include_hidden:true include_missing:true include_suppressed_by_age:true include_deleted:true'
    #fql = 'kind:Group AND title:Billing and Title Clerks include_stale:true include_hidden:true include_missing:true include_suppressed_by_age:true include_deleted:true'
    jsonz = {"fql": fql, "page": 1, "limit": 1000}
    #filter_expr = "kind:Group AND title='{value}'"


    #base = (f"{BASE_URL}" + tenant_id + "/assets")
    #All_Groups = USE.get_all_assets_from_fql(base=base, headers=headers, jsonz=jsonz)
    All_Groups = input_all_groups()
    fql_2 = 'kind:User include_stale:true include_hidden:true include_missing:true include_suppressed_by_age:true include_deleted:true'
    #jsonz = {"fql": fql_2, "page": 1, "limit": 1000}
    all_users_master = input_user_data()
    print("User Count:  ", len(all_users_master))
    #all_users_master = USE.get_all_assets_from_fql(base=base, headers=headers, jsonz=jsonz)
    b_tier_0_groups = []
    print("All Group Length: ", len(All_Groups))
    for btg in All_Groups:
        if btg.get("group") is not None:
            if btg.get("title") in input_groups_dict:
                b_tier_0_groups.append(btg)
                input_groups_set.remove(btg.get("title"))

    missing_groups = list(input_groups_set)
    print("B-Tier-0 Group Length: ", len(b_tier_0_groups))

    """
    all_users = []
    all_users_uid: dict[str, list] = defaultdict(list)
    other_classes = []
    ad_users_master_list = []
    ad_groups_no_members = []
    en_ids_master_list = []
    en_groups_no_members = []
    groups_found_classes = []
    for b_tier_0_g in b_tier_0_groups:
        classes = b_tier_0_g["group"].get("nested_classes")
        if classes is None:
            print(b_tier_0_g.get("title"))
        if classes is not None:
            for n_class in classes:
                if n_class == "Active-Directory-Group":
                    groups_found_classes.append(n_class)
                    ad_keys_list = b_tier_0_g["group"]["active_directory_group"].get("members")
                    if ad_keys_list is not None:
                        ad_users_master_list.extend(ad_keys_list)
                    if ad_keys_list is None:
                        ad_groups_no_members.append(b_tier_0_g)
                elif n_class == "Microsoft-Entra-Group":
                    groups_found_classes.append(n_class)
                    en_dict_keys_list = b_tier_0_g["group"]["microsoft_entra_group"].get("members")
                    en_keys_list = []
                    if en_dict_keys_list is not None:
                        for dict_key in en_dict_keys_list:
                            en_keys_list.append(dict_key.get("id"))
                        en_ids_master_list.extend(en_keys_list)
                    if en_dict_keys_list is None:
                        en_groups_no_members.append(b_tier_0_g)
                else:
                    groups_found_classes.append(n_class)
                    print(f"Class Not Found: {n_class}   For Group: {b_tier_0_g}")
                    other_classes.append(n_class)
                    
    ad_users_master_dict = dict.fromkeys(ad_users_master_list)
    en_ids_master_dict = dict.fromkeys(en_ids_master_list)
    """
    master_dict_all_data, master_discrep = USE.members_from_asm_groups(b_tier_0_groups)
    group_members = master_dict_all_data["group_members"]
    all_users_uid, dn_str_keys, member_dict_to_id = USE.clean_asm_group_members(group_members, all_users_master)
    while len(dn_str_keys) > 0 or len(member_dict_to_id) > 0:
        continue

    #print(f"Number of AD Users: {len(ad_users_master_dict)}")
    #ad_filter_xpr = 'kind:User AND json("$.active_directory_user.distinguished_name") = "{value}"'
    #ad_users, missing_ad_users = USE.aggregate_assets_from_values_list(values=list(ad_users_master_set), headers=headers, base_url=base, filter_expression=ad_filter_xpr, evaluate_output=False)

    #print(f"Number of Entra Users: {len(en_ids_master_dict)}")
    #en_filter_xpr = 'kind:User AND json("$.microsoft_entra_user.id") = "{value}"'
    #ed_users, missing_en_users = USE.aggregate_assets_from_values_list(values=list(en_ids_master_set), headers=headers, base_url=base, filter_expression=en_filter_xpr, evaluate_output=False)
    """ 
   neat_classes = dict.fromkeys(groups_found_classes)
    user_classes = []
    for gr_class in neat_classes:
        user_classes.append(USE.group_to_user(USE.clean_class(gr_class)))
    """
    """ 
    all_user_by_dn_keyed = {}
    all_user_by_entra_id_keyed = {}
    pop_dn = 0
    pop_en = 0
    for user in all_users_master:
        if user.get("user") is not None:
            if user["user"].get("active_directory_user") is not None:
                if user["user"]["active_directory_user"].get("distinguished_name") in ad_users_master_dict:
                    all_users_uid[user.get("uid")].append(user["user"]["active_directory_user"].get("distinguished_name"))
                    ad_users_master_dict.pop(user["user"]["active_directory_user"].get("distinguished_name"))
                    pop_dn = pop_dn + 1
                    all_user_by_dn_keyed[user["user"]["active_directory_user"].get("distinguished_name")] = user
            if user["user"].get("microsoft_entra_user") is not None:
                if user["user"]["microsoft_entra_user"].get("id") in en_ids_master_dict:
                    all_users_uid[user.get("uid")].append(user["user"]["microsoft_entra_user"].get("id"))
                    en_ids_master_dict.pop(user["user"]["microsoft_entra_user"].get("id"))
                    pop_en = pop_en + 1
                    all_user_by_entra_id_keyed[user["user"]["microsoft_entra_user"].get("id")] = user

        else:
            print(user.get("title"))
    """



    print("Group Missing:  ", missing_groups, "\n")
    print("AD Users Missing:  ", list(dn_str_keys), "\n")
    print("Entra Users Missing:  ", list(member_dict_to_id), "\n")
    #print(f"Popped DN Count: {pop_dn}")
    #print(f"Popped ENTRA Count: {pop_en}")
    #print("Groups Found Classes:  ", list(neat_classes), "\n")
    original_stdout = sys.stdout
    path = "C:/Users/justin.schuessler/Documents/API_Output/Sedara_ASM/"
    Fullpath = path + "ASM_WH_ALL_B_Tier_0_Group_Users_v_2.json"
    f = open(Fullpath, "w")
    sys.stdout = f
    output = json.dumps(all_users_uid, indent=4, )
    print(output)
    f.close()
    sys.stdout = original_stdout

