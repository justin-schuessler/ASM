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
    all_g_by_dn_keyed = {}
    all_g_by_entra_id_keyed = {}
    print("All Group Length: ", len(All_Groups))
    for btg in All_Groups:
        if btg.get("group") is not None:
            if btg.get("title") in input_groups_dict:
                b_tier_0_groups.append(btg)
                input_groups_set.remove(btg.get("title"))
            if btg["group"].get("microsoft_entra_group") is not None:
                all_g_by_entra_id_keyed[btg["group"]["microsoft_entra_group"].get("id")] = btg
            if btg["group"].get("active_directory_group") is not None:
                all_g_by_dn_keyed[btg["group"]["active_directory_group"].get("distinguished_name")] = btg

    missing_groups = list(input_groups_set)
    print("B-Tier-0 Group Length: ", len(b_tier_0_groups))

    master_dict_all_data, master_discrep = USE.members_from_asm_groups(b_tier_0_groups)
    group_members = master_dict_all_data.get("group_members")
    all_users_uid, dn_str_keys, member_dict_to_id = USE.clean_asm_group_members(group_members, all_users_master, master_dict_all_data.get("user_nested_classes"))
    all_group_emails_dict = master_dict_all_data.get("group_emails")
    c = 0
    while len(dn_str_keys) > 0 or len(member_dict_to_id) > 0:
        dn_str_keys_popper = dict(dn_str_keys)
        member_dict_to_id_popper = dict(member_dict_to_id)
        more_g = []
        mini_data = {}
        mini_discrep = {}
        mini_dn_str_keys = {}
        mini_member_dict_to_id = {}
        mini_all_users_uid = {}
        mini_grp_email = {}
        for dn in dn_str_keys:
            if dn in all_g_by_dn_keyed:
                more_g.append(all_g_by_dn_keyed.get(dn))
                dn_str_keys_popper.pop(dn)
        for en_id in member_dict_to_id:
            if en_id in all_g_by_entra_id_keyed:
                more_g.append(all_g_by_entra_id_keyed.get(en_id))
                member_dict_to_id_popper.pop(en_id)

        mini_data, mini_discrep = USE.members_from_asm_groups(more_g)
        master_dict_all_data["group_nested_classes"] = master_dict_all_data["group_nested_classes"] | mini_data["group_nested_classes"]
        master_dict_all_data["groups_no_members"] = master_dict_all_data["groups_no_members"] | mini_data["groups_no_members"]
        master_dict_all_data["user_nested_classes"] = master_dict_all_data["user_nested_classes"] | mini_data["user_nested_classes"]
        mini_g_emails = mini_data.get("group_emails")
        for grp_t in mini_g_emails.keys():
            if all_group_emails_dict.get(grp_t) is not None:
                all_group_emails_dict[grp_t] = all_group_emails_dict.get(grp_t) | mini_g_emails.get(grp_t)
            if all_group_emails_dict.get(grp_t) is None:
                all_group_emails_dict[grp_t] = mini_g_emails.get(grp_t)

        mini_all_users_uid, mini_dn_str_keys, mini_member_dict_to_id = USE.clean_asm_group_members(mini_data["group_members"], all_users_master, master_dict_all_data.get("user_nested_classes"))
        master_dict_all_data["group_members"].extend(mini_data["group_members"])
        dn_str_keys = dn_str_keys_popper | mini_dn_str_keys
        member_dict_to_id = member_dict_to_id_popper | mini_member_dict_to_id
        for record in mini_all_users_uid:
            a_l = all_users_uid.get(record)
            m_a_l = mini_all_users_uid.get(record)
            all_users_uid[record].extend(mini_all_users_uid.get(record))
            a_l_plus = set(all_users_uid.get(record))
            all_users_uid[record] = list(a_l_plus)
        c = c + 1
        print(f"Loop Count: {c}")
        if c > 5:
            break

    if len(missing_groups) > 0:
        print("Group Missing :  ", missing_groups)
    print("AD Users Missing count :  ", len(dn_str_keys))
    print("Entra Users Missing count:  ", len(member_dict_to_id))
    if len(dn_str_keys) > 0:
        print("AD Users Missing:  ", dn_str_keys, "\n")
    if len(member_dict_to_id) > 0:
        print("Entra Users Missing:  ", member_dict_to_id, "\n")
    print("Number of Users UID:  ", len(all_users_uid))
    if len(master_dict_all_data.get("groups_no_members")) > 0:
        print("Groups With No Members:  ", master_dict_all_data.get("groups_no_members"))
    print("Number of groups in Emails List:  ", len(all_group_emails_dict))

    for e_set in all_group_emails_dict.keys():
        if all_group_emails_dict.get(e_set) is not None:
            all_group_emails_dict[e_set] = list(all_group_emails_dict.get(e_set))
    output_data = {
        "all_users": all_users_uid,
        "all_groups_emails": all_group_emails_dict
    }

    #print("Groups Found Classes:  ", list(neat_classes), "\n")
    original_stdout = sys.stdout
    path = "C:/Users/justin.schuessler/Documents/API_Output/Sedara_ASM/"
    Fullpath = path + "ASM_WH_ALL_B_Tier_0_Group_Users_v_3.json"
    f = open(Fullpath, "w")
    sys.stdout = f
    output = json.dumps(output_data, indent=4, )
    print(output)
    f.close()
    sys.stdout = original_stdout

