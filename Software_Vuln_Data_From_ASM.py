import sys
import json
import datetime
import requests
from requests.auth import HTTPBasicAuth
import subprocess
import Useful_ASM_functions as USE
import get_1password_field


if __name__ == "__main__":
    original_stdout = sys.stdout

    #tenant_id = get_1password_field.get_1password_field("Sedara Platform ASM API", "sedara tenant id", "API")

    access_key = USE.get_asm_platform_api_access_key()
    headers = {"Authorization": f"Bearer {access_key}",
               "Content-Type": "application/json"}
    
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
    tenant_id = "ca25595c-c6f0-4c58-9e9b-c83325eb9cc6"

    #Noco
    #tenant_id = "b1bf38e6-4f2f-4fbc-8432-53d3a1fc1379"

    #Taylor Devices
    #tenant_id = "83b83e29-f7ed-4588-a271-a8604522160c"

    path = "C:/Users/justin.schuessler/Documents/API_Output/Sedara_ASM/"

    data = USE.get_software_vuln_data(headers=headers, tenant_id=tenant_id)


    Fullpath = path + "West_Herr_Software_Vuln_data_via_ASM.json"
    f = open(Fullpath, "w")
    sys.stdout = f
    output = json.dumps(data, indent=4, )
    print(output)
    f.close()
    sys.stdout = original_stdout

    path = "C:/Users/justin.schuessler/Documents/API_Output/Sumo/"