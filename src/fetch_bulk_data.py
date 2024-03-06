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
TODAY = datetime.today().strftime("%Y%m%d")


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
    filepath = f"{DIRECTORY}/{name}_{TODAY}.json"
    print(f"Saving file to '{filepath}'...")
    with open(filepath, "w") as outfile:
        outfile.write(json.dumps(file))
    print(f"Successfully saved file to '{filepath}'.")


def open_json(filepath):
    with open(filepath) as infile:
        return json.load(infile)


def ensure_dir_exists():
    if not os.path.isdir(DIRECTORY):
        os.makedirs(DIRECTORY)


def clear_old_files(filename, force=False):
    ensure_dir_exists()
    with os.scandir(DIRECTORY) as it:
        for entry in it:
            if entry.name != "README.md" and (
                entry.name.split("_")[0] == filename
                and (force or entry.name.split("_")[1].split(".")[0] != TODAY)
            ):
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
    if (
        filename in [i.name.split("_")[0] for i in os.scandir(DIRECTORY)]
        and force is False
    ):
        print(f"Up-to-date data already exists. ({filename})")
        return 0
    data = [i for i in func(uri) if i["legalities"]["commander"] == "legal"]
    write_to_json(data, filename)
    return 1


def fetch(force=False):
    uri = get_download_uri()
    filename = "oracle-cards"
    clear_old_files(filename, force)
    get_data_if_none_exists(filename, uri, get_data, force)


def fetch_all_commanders(force=False):
    uri = "https://api.scryfall.com/cards/search?q=is%3Acommander+legal%3Acommander"
    filename = f"all-commanders"
    clear_old_files(filename, force)
    get_data_if_none_exists(filename, uri, paginate, force)


def main():
    fetch()
    fetch_all_commanders()


if __name__ == "__main__":
    main()
