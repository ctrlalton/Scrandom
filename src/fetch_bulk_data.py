import requests
import json
import os
from datetime import datetime
from pathlib import Path
import time

TYPE = "oracle-cards"
CWD = Path.cwd()
MOD_PATH = Path(__file__).parent
REL_PATH = "../output/bulk_data"
DIRECTORY = (MOD_PATH / REL_PATH).resolve()


def get_download_uri():
    print("Fetching download URI...")
    x = requests.get(f"https://api.scryfall.com/bulk-data/{TYPE}").json()[
        "download_uri"
    ]
    print(f"Successfully fetched download URI: '{x}'")
    return x


def get_data(uri):
    print(f"Retrieving data from '{uri}'...")
    x = requests.get(uri).json()
    print(f"Successfully downloaded file at '{uri}'.")
    return x


def write_to_json(file, name):
    filepath = f"{DIRECTORY}/{name}"
    print(f"Saving file to '{filepath}'...")
    with open(filepath, "w") as outfile:
        outfile.write(json.dumps(file))
    print(f"Successfully saved file to '{filepath}'.")


def ensure_dir_exists():
    if not os.path.isdir(DIRECTORY):
        os.makedirs(DIRECTORY)

def clear_directory(filename, force=False):
    ensure_dir_exists()
    with os.scandir(DIRECTORY) as it:
        for entry in it:
            if entry.name.split("_")[0] != filename.split("_")[0]:
                continue
            if entry.name != filename or force:
                os.remove(entry)


def paginate(uri):
    file = get_data(uri)
    total = file["total_cards"]
    all_data = []

    while True:
        all_data += [i for i in file["data"]]
        if not "next_page" in dict.keys(file):
            break
        time.sleep(0.1)
        file = get_data(file["next_page"])
    assert total == len(all_data)

    return all_data


def get_data_if_none_exists(filename, uri, func, force=False):
    if filename in [i.name for i in os.scandir(DIRECTORY)] and force is False:
        print("Up-to-date data already exists. Download was skipped.")
        return 0
    data = func(uri)
    write_to_json(data, filename)
    return 1


def fetch(force=False):
    uri = get_download_uri()
    filename = f"oracle-cards_{datetime.today().strftime('%Y%m%d')}.json"
    clear_directory(filename, force)
    get_data_if_none_exists(filename, uri, get_data, force)


def fetch_all_commanders(force=False):
    uri = "https://api.scryfall.com/cards/search?q=is%3Acommander+legal%3Acommander"
    filename = f"all-commanders_{datetime.today().strftime('%Y%m%d')}.json"
    clear_directory(filename, force)
    get_data_if_none_exists(filename, uri, paginate, force)


def main():
    fetch()
    fetch_all_commanders(force=True)


if __name__ == "__main__":
    main()
