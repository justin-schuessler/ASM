import csv
import io


def clean_class(nested):
    clean = nested.lower().replace("-", "_")
    return clean


# returns default user lookup table structure
# can also be modified to increase the counts of some fields
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


def asm_users_to_sumo_lookup_csv(all_users: dict):
    fields, counts = get_asm_user_default_lookup_table_structure()
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
            for d_u_c in user["user"].get("nested_classes"):
                u_c = clean_class(d_u_c)
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
                print(f"UPN Account Issue:  {title}  |  Has UPN Count: {len(user_principal_name)}")
                if len(user_principal_name) > found_upn_count:
                    found_upn_count = len(user_principal_name)
            user_row = []
            user_row.append(list(user_principal_name))
            user_row.append(list(sam_accounts))
            user_row.append(title)
            user_row.append(list(emails))

            rows.append(user_row)

    new_counts = {"upn_count": found_upn_count, "sam_count": found_sam_count, "email_count": found_e_count}
    fields, counts = get_asm_user_default_lookup_table_structure(counts=new_counts)
    writer.writerow(field["fieldName"] for field in fields)
    out_rows = []
    for r in rows:
        print("Dirty:  ",r)
        upn_out = r[0]
        sams_out = r[1]
        title_out = r[2]
        emails_out = r[3]
        clean_user_row = []
        upn_c = 0
        sams_c = 0
        emails_c = 0
        for o_upn in range(counts.get("upn_count")):
            if len(upn_out) > upn_c:
                clean_user_row.append(upn_out[o_upn])
            else:
                clean_user_row.append("")
            upn_c = upn_c + 1

        for o_sams in range(counts.get("sam_count")):
            if len(sams_out) > sams_c:
                clean_user_row.append(sams_out[o_sams])
            else:
                clean_user_row.append("")
            sams_c = sams_c + 1

        clean_user_row.append(title_out)

        for o_emails in range(counts.get("email_count")):
            if len(emails_out) > emails_c:
                clean_user_row.append(emails_out[o_emails])
            else:
                clean_user_row.append("")
            emails_c = emails_c + 1
        print("Cleaned: ",clean_user_row)
        out_rows.append(clean_user_row)

    writer.writerows(out_rows)
    return output.getvalue(), fields, counts
