import sys
from datetime import date, datetime
import get_1password_field as get_1
import Useful_ASM_functions as USE
import Useful_functions as UF


def get_all_asm_users_for_customer(tenant_id: str, filename: str):
    access_key = USE.get_asm_platform_api_access_key()
    headers = {"Authorization": f"Bearer {access_key}",
               "Content-Type": "application/json"}
    jsonz = {"fql": USE.get_all_user_fql(), "page": 1, "limit": 1000}
    all_users_master = USE.get_all_assets_from_fql(headers=headers, tenant_id=tenant_id, jsonz=jsonz)
    UF.out_to_json(dict=all_users_master, filename=(USE.get_asm_out_path() + filename), original_stdout=original_stdout)
    return all_users_master


if __name__ == "__main__":
    args = sys.argv
    original_stdout = sys.stdout
    one_pass_sumo_dict = None
    if len(args) > 1:
        item_name = args[1]
    else:
        item_name = input("Input Item Name: ")
    file = str(datetime.now().strftime("%Y-%m-%d_%H-%M")) + item_name.split("-")[1] + "_all_users.json"
    while one_pass_sumo_dict is None:
        try:
            one_pass_sumo_dict = get_1.get_1password_1_sumo_item(item_name=item_name, vault="API")
        except:
            item_name = input("Input Item Name: ")

    get_all_asm_users_for_customer(tenant_id=one_pass_sumo_dict.get("asm_tenant_id"), filename=file)

