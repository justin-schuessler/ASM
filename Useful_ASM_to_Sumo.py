import sys
import json
import csv
import io
import datetime
import requests
import time
from requests.auth import HTTPBasicAuth
import subprocess
import get_1password_field
import os
from openpyxl import Workbook
from collections import Counter
from collections import defaultdict
import Useful_ASM_functions as USE


def get_asm_user_default_lookup_table_structure(counts=None) -> tuple[list, dict]:
    fields = []
    if counts is None:
        counts = {"upn_count": 1, "sam_count": 1, "email_count": 3}

    if counts.get("upn_count") > 1:
        for upn_c in range(counts.get("upn_count")):
            upn_d = {
                "fieldName": "user_principal_name_" + str(upn_c + 1),
                "fieldType": "string"
            }
            fields.append(upn_d)
    if counts.get("upn_count") == 1:
        fields.append({
            "fieldName": "user_principal_name",
            "fieldType": "string"
        })

    if counts.get("sam_count") > 1:
        for sam_c in range(counts.get("sam_count")):
            sam_d = {
                "fieldName": "sam_account_name_" + str(sam_c + 1),
                "fieldType": "string"
            }
            fields.append(sam_d)
    if counts.get("sam_count") == 1:
        fields.append({
            "fieldName": "sam_account_name",
            "fieldType": "string"
        })
    fields.append(
        {
            "fieldName": "title",
            "fieldType": "string"
        })
    for e in range(counts.get("email_count")):
        d = {
            "fieldName": "email_"+str(e+1),
            "fieldType": "string"
        }
        fields.append(d)
    return fields, counts


def get_csv_format_of_default_lookup_table_structure(counts=None):
    fields, counts = get_asm_user_default_lookup_table_structure(counts=counts)
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(field["fieldName"] for field in fields)
    return output.getvalue(), counts


def asm_users_to_sumo_lookup_csv(all_users: dict, user_classes: list) -> str:
    first_line, counts = get_csv_format_of_default_lookup_table_structure()
    upn_count = counts.get("upn_count")
    sam_count = counts.get("sam_count")
    email_count = counts.get("email_count")

    get_list = ["on_premises_sam_account_name", "on_premises_user_principal_name", "email", "sam_account_name", "user_principal_name"]

    found_upn_count = 1
    found_sam_count = 1
    found_e_count = 3
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    rows = []
    for user in all_users:
        sam_accounts = set()
        user_principal_name = set()
        title = user.get("title")
        emails = set()
        if user.get("user") is not None:
            for u_c in USE.clean_class(user.get("nested_classes")):
                class_emails = []
                for item in get_list:
                    value = user["user"][u_c].get(item)
                    if value is not None:
                        if item == "on_premises_sam_account_name" or item == "sam_account_name":
                            sam_accounts.add(value)
                        if item == "on_premises_user_principal_name" or item == "user_principal_name":
                            user_principal_name.add(value)
                        if item == "email" and isinstance(value, list):
                            for e in value:
                                class_emails.append(e)
                emails = emails | set(class_emails)

            if len(emails) > email_count:
                if len(emails) > 50:
                    print(f"Email Length Issue:  {title}  |  Has Email Count: {len(emails)} ")
                if len(emails) > found_e_count:
                    found_e_count = len(emails)
            if len(sam_accounts) > sam_count:
                print(f"Sam Account Issue:  {title}  |  Has Sam Count: {len(sam_accounts)}")
                if len(sam_accounts) > found_sam_count:
                    found_sam_count = len(sam_accounts)
            if len(user_principal_name) > upn_count:
                print(f"UPN Account Issue:  {title}  |  Has UPN Count: {len(sam_accounts)}")
                if len(user_principal_name) > found_upn_count:
                    found_upn_count = len(user_principal_name)
            user_row = []
            for upn_a in list(user_principal_name):
                user_row.append(upn_a)
            for sam_a in list(sam_accounts):
                user_row.append(sam_a)
            user_row.append(title)
            for em_a in list(emails):
                user_row.append(em_a)
            rows.append(user_row)

    new_counts = {"upn_count": found_upn_count, "sam_count": found_sam_count, "email_count": found_e_count}
    first_line, counts = get_csv_format_of_default_lookup_table_structure(counts=new_counts)
    writer.writerow(first_line)
    writer.writerows(rows)
    return output.getvalue()
