import subprocess


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