import requests
import json
import os
from datetime import datetime
from pathlib import Path

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
    print(f"Downloading file at '{uri}'...")
    x = requests.get(uri).json()
    print(f"Successfully downloaded file at '{uri}'.")
    return x


def write_to_json(file, name):
    filepath = f"{DIRECTORY}/{name}"
    print(f"Saving file to '{filepath}'...")
    with open(filepath, "w") as outfile:
        outfile.write(json.dumps(file))
    print(f"Successfully saved file to '{filepath}'.")


def validate_directory(filename):
    if not os.path.isdir(DIRECTORY):
        os.mkdir(DIRECTORY)
    with os.scandir(DIRECTORY) as it:
        for entry in it:
            if entry.name.split("_")[0] != filename.split("_")[0]:
                continue
            if entry.name != filename:
                os.remove(entry)


def paginate(uri):
    file = get_data(uri)
    total = file["total_cards"]
    all_data = []

    while True:
        all_data += [i["name"] for i in file["data"]]
        if not "next_page" in dict.keys(file):
            break
        file = get_data(file["next_page"])
    assert total == len(all_data)

    return all_data


def get_data_if_none_exists(filename, uri, func):
    if filename not in [i.name for i in os.scandir(DIRECTORY)]:
        data = func(uri)
        write_to_json(data, filename)
    else:
        print("Up-to-date data already exists. Download was skipped.")


def fetch():
    uri = get_download_uri()
    filename = f"oracle-cards_{datetime.today().strftime('%Y%m%d')}.json"
    validate_directory(filename)
    get_data_if_none_exists(filename, uri, get_data)


def fetch_all_commanders():
    uri = "https://api.scryfall.com/cards/search?q=is%3Acommander"
    filename = f"all-commanders_{datetime.today().strftime('%Y%m%d')}.json"
    validate_directory(filename)
    get_data_if_none_exists(filename, uri, paginate)


def main():
    fetch()
    fetch_all_commanders()


if __name__ == "__main__":
    main()
