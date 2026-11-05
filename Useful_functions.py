import os
import json
import requests
import logging
import base64
from requests.auth import HTTPBasicAuth
import sys
from pathlib import Path
from openpyxl import Workbook

path = "/Sumo_Maintnance_and_Health_project/Sedara-sumo-catalog/"
proj_cache_path = "C:/Users/justin.schuessler/Documents/SumoLogic/Project_cache/"
sumo_catalog_dir = "/Sumo_Maintnance_and_Health_project/cloud-siem-content-catalog"

def get_sumo_siem_catalog_dir():
    return sumo_catalog_dir

def get_project_cache_path():
    return proj_cache_path


def get_project_path():
    return path


# opens json type file and returns object
def load_json(file):
    with open(file, 'r') as json_file:
        data = json.load(json_file)
    return data


# saves json file
def out_to_json(dict, filename, original_stdout):
    saved_location = str(Path(filename).parent)
    file = str(Path(filename).name)
    f = open(filename, "w")
    sys.stdout = f
    output = json.dumps(dict, indent=4, )
    print(output)
    f.close()
    sys.stdout = original_stdout
    print(file, "  | Saved to | " + saved_location + "  | Folder ")


def rules_out_to_excel(data, xl_save_path):
    wb = Workbook()
    ws = wb.active
    row = 2

    ws["A1"] = "Rule ID"
    ws["B1"] = "Rule Name"
    ws["C1"] = "Rule Type"
    ws["D1"] = "Rule Description Expression"
    ws["E1"] = "Rule Summary Expression"
    ws["F1"] = "Rule Match Expression"
    ws["G1"] = "Entity Selector"
    ws["H1"] = "Group By Field"

    for rule in data:
        configed_dict = rule.get("configured_integrations_list")
        if len(configed_dict) > 0:
            for configed_integration in rule.get("configured_integrations_list").keys():
                ws.cell(row=row, column=1).value = rule
                ws.cell(row=row, column=2).value = rule.get("name")
                ws.cell(row=row, column=3).value = rule["configured_integrations_list"][configed_integration].get("name")
                ws.cell(row=row, column=4).value = configed_integration
                ws.cell(row=row, column=5).value = rule["configured_integrations_list"][configed_integration].get("healthy")
                ws.cell(row=row, column=6).value = rule["configured_integrations_list"][configed_integration].get("state")
                status_string = ", ".join(rule["configured_integrations_list"][configed_integration].get("status_list"))
                ws.cell(row=row, column=7).value = status_string
                ws.cell(row=row, column=8).value = rule["configured_integrations_list"][configed_integration].get("last_seen")
                row += 1

    wb.save(xl_save_path)