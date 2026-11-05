import subprocess
import json


def get_1password_field(item_name: str, field: str, vault: str) -> str:
    """
    Fetch a single field from a 1Password item using the CLI.

    :param item_name: Name of the 1Password item
    :param field: Field name to fetch ("username", "password", custom field)
    :param vault: Vault name
    :return: Field value as string
    """
    try:
        result = subprocess.run(["op", "item", "get", item_name, "--vault", vault, "--field", field], capture_output=True, text=True, check=True )
        return result.stdout.strip()

    except subprocess.CalledProcessError as e:
        print(f"Error fetching field '{field}' from item '{item_name}' in vault '{vault}':")
        print(e.stderr)
        raise


def get_1password_item(item_name: str, vault: str):
    try:
        result = subprocess.run(["op", "item", "get", item_name, "--vault", vault, "--format", "json"], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error fetching vault '{vault}':")
        print(e.stderr)
        raise


def get_1password_1_sumo_item(item_name: str, vault: str):
    """
     Returns 1 Sumo API Creds FROM 1pass
     In a dictionary
    {
        "tenant_name":                  "abc",
        "Access ID":                    "efg",
        "Access Key":                   "secret",
        "url":                          "url",
        "Org ID":                       "000001938",
        "Customer_Configs_folder_id":   "992084",
        "Admin_Folder_id":              "30477"
        "asm_tenant_id":                "373939-3848995-2948"
    }
    """
    item = get_1password_item(item_name=item_name, vault=vault)
    sumo_onepass_dict = {}
    sumo_onepass_dict["tenant_name"] = item.get("title").split(" - ")[1].strip()
    for field in item.get("fields"):
        if field.get("label") == "Access ID":
            sumo_onepass_dict["Access ID"] = field.get("value")
        if field.get("label") == "Access Key":
            sumo_onepass_dict["Access Key"] = field.get("value")
        if field.get("label") == "url":
            sumo_onepass_dict["url"] = field.get("value")
        if field.get("label") == "Org ID":
            sumo_onepass_dict["Org ID"] = field.get("value")
        if field.get("label") == "Admin_Folder_id":
            sumo_onepass_dict["Admin_Folder_id"] = field.get("value")
        if field.get("label") == "Customer_Configs_folder_id":
            sumo_onepass_dict["Customer_Configs_folder_id"] = field.get("value")
        if field.get("label") == "asm_tenant_id":
            sumo_onepass_dict["asm_tenant_id"] = field.get("value")
    return sumo_onepass_dict


def get_all_1password_items(vault: str):
    try:
        result = subprocess.run(["op", "item", "list", "--vault", "API", "--format", "json"], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    except subprocess.CalledProcessError as e:
        print(f"Error fetching vault '{vault}':")
        print(e.stderr)
        raise


def get_sumo_1password_items_filtered(vault: str):
    """
    Returns all Sumo API Creds FROM 1pass
    In a list of dictionary
    [
        {
            "tenant_name":                  "abc"
            "Access ID":                    "efg"
            "Access Key":                   "secret"
            "url":                          "url"
            "Org ID":                       "000001938"
            "Customer_Configs_folder_id":   "992084",
            "Admin_Folder_id":              "30477"
            "asm_tenant_id":                "373939-3848995-2948"
        }
    ]
    """
    all_api_items = get_all_1password_items(vault)
    onepass_cred_list = []
    for item in all_api_items:
        if item.get("title").upper().startswith("SUMO -"):
            onepass_item = get_1password_item(item_name=item.get("title"), vault=vault)
            sumo_onepass_dict = {}
            sumo_onepass_dict["tenant_name"] = item.get("title").split(" - ")[1].strip()
            for field in onepass_item.get("fields"):
                if field.get("label") == "Access ID":
                    sumo_onepass_dict["Access ID"] = field.get("value")
                if field.get("label") == "Access Key":
                    sumo_onepass_dict["Access Key"] = field.get("value")
                if field.get("label") == "url":
                    sumo_onepass_dict["url"] = field.get("value")
                if field.get("label") == "Org ID":
                    sumo_onepass_dict["Org ID"] = field.get("value")
                if field.get("label") == "Admin_Folder_id":
                    sumo_onepass_dict["Admin_Folder_id"] = field.get("value")
                if field.get("label") == "Customer_Configs_folder_id":
                    sumo_onepass_dict["Customer_Configs_folder_id"] = field.get("value")
                if field.get("label") == "asm_tenant_id":
                    sumo_onepass_dict["asm_tenant_id"] = field.get("asm_tenant_id")

            onepass_cred_list.append(sumo_onepass_dict)
    return onepass_cred_list