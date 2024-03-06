import requests
import json
import os
from datetime import datetime

DIRECTORY = "bulk_data"
TYPE = "oracle-cards"


def get_download_uri():
    print("Fetching download URI...")
    x = requests.get(f"https://api.scryfall.com/bulk-data/{TYPE}").json()[
        "download_uri"
    ]
    print(f"Successfully fetched download URI: '{x}'")
    return x


def get_bulk_data(uri):
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


def fetch():
    uri = get_download_uri()
    filename = os.path.basename(uri).split("/")[-1]
    if not os.path.isdir(DIRECTORY):
        os.mkdir(DIRECTORY)
    with os.scandir(DIRECTORY) as it:
        for entry in it:
            if entry.name != filename:
                os.remove(entry)
    if len(os.listdir(DIRECTORY)) == 0:
        data = get_bulk_data(uri)
        write_to_json(data, filename)
    else:
        print("Up-to-date data already exists. Download was skipped.")


def main():
    fetch()


if __name__ == "__main__":
    main()
