import sys
import json
import datetime
import requests
from requests.auth import HTTPBasicAuth
import subprocess
import get_1password_field


if __name__ == "__main__":
    original_stdout = sys.stdout

    #tenant_id = get_1password_field.get_1password_field("Sedara Platform ASM API", "sedara tenant id", "API")

    access_key = get_1password_field.get_1password_field("Sedara Platform ASM API", "Access key", "API")

    
    #derrick_corp
    #tenant_id = "54fbf0fd-6c1f-4c9a-9013-d61b33bf272f"
    
    #Williamsville
    #tenant_id = "fbaebcab-ce26-4db4-9dcb-862adb0272b6"
    
    #cleve Hill
    #tenant_id = "018ae841-85af-7872-aa44-4d307ad60b86"

    #esquire
    #tenant_id = "0193f4ab-8052-7b07-92ac-18c888ed6904"

    #pathfinder
    #tenant_id = "be2d58fb-f91f-453a-a4a6-6851402a98d4"

    #west herr
    #tenant_id = "ca25595c-c6f0-4c58-9e9b-c83325eb9cc6"

    #Noco
    #tenant_id = "b1bf38e6-4f2f-4fbc-8432-53d3a1fc1379"

    #Taylor Devices
    tenant_id = "83b83e29-f7ed-4588-a271-a8604522160c"

    path = "C:/Users/justin.schuessler/Documents/API_Output/Sedara_ASM/"

    BASE_URL = "https://platform.sedaraapis.com/asm/"
    headers = {"Authorization":  f"Bearer {access_key}",
               "Content-Type": "application/json"}
    """jsonz = {"page": 1, "limit": 10}"""

    #kind = 'kind:Device (duo_phone.capabilities ~ "%sms%") AND (duo_phone.capabilities ~ "%phone%") AND (duo_phone.capabilities !~ "%auto%") AND (duo_phone.capabilities !~ "%push%") AND (duo_phone.capabilities !~ "%mobile_otp%")'
    #kind = 'kind:User AND class:SumoLogic-CSE-Entity AND json("$.active_directory_user.user_principal_name") = "khibbert@pathfinderbank.com"'
    #kind = 'kind:Group'
    #kind = 'title:ATL-QCBIND3'
    #kind = 'class:SumoLogic-CSE-Entity'
    #kind = 'class:Active-Directory-Group'
    #kind = '(class:Active-Directory-Computer OR class:Active-Directory-Group OR class:Active-Directory-User)include_stale:true include_hidden:true include_missing:true include_suppressed_by_age:true include_deleted:true'
    kind = 'kind:@device'
    jsonz = {"fql": kind, "page": 1, "limit": 1000}

    response = requests.post(f"{BASE_URL}" + tenant_id + "/assets", headers=headers, json=jsonz)
    print("Status:", response.status_code)
    #print("Response:", response.text)

    response.raise_for_status()
    print(response.status_code)
    data = response.json()

    #print(len(data.get("assets")))

    Fullpath = path + "ASM_AD_Taylor_Devices_All_Devices_1.json"
    f = open(Fullpath, "w")
    sys.stdout = f
    output = json.dumps(data, indent=4, )
    print(output)
    f.close()
    sys.stdout = original_stdout

    path = "C:/Users/justin.schuessler/Documents/API_Output/Sumo/"