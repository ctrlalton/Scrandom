import requests
import json
import os
from datetime import datetime
from pathlib import Path
import time
import re
import random

TYPE = "oracle-cards"
TODAY = datetime.today().strftime("%Y%m%d")

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


def get_file_name(name):
    with os.scandir(DIRECTORY) as it:
        for entry in it:
            if entry.name.split("_")[0] == name:
                return entry.name
    return None


def clean_name(name):
    clean_name = re.sub(
        "[.,'<>:\"/\\|?*]",
        "",
        str(name)
        .replace(" // ", "_")
        .replace(" ", "_")
        .replace("-", "_")
        .replace("&", "and"),
    )
    return clean_name


def deck_add_message(card_type, name):
    print(f'{card_type}:\tAdding "{name}" to your deck...'.expandtabs(25))


def get_random_commander(color_identity=None, silent=False):
    filename = get_file_name("all-commanders")
    filepath = f"{DIRECTORY}/{filename}"
    commanders = open_json(filepath)
    if color_identity is not None:
        commanders = [
            i for i in commanders if set(i["color_identity"]) == set(color_identity)
        ]
    x = random.choice(commanders)
    if not silent:
        deck_add_message("COMMANDER", x["name"])
    return x


def get_color_set(color_identity):
    filename = get_file_name("oracle-cards")
    filepath = f"{DIRECTORY}/{filename}"
    cards = open_json(filepath)
    cards = [
        i
        for i in cards
        if set(i["color_identity"]) <= set(color_identity)
        and i["legalities"]["commander"] == "legal"
    ]
    return cards


def get_random_card(cards, silent=False):
    x = random.choice(cards)
    typex = x["type_line"].split("—")[0].strip()
    if not silent:
        deck_add_message(typex, x["name"])
    return x


def generate_commander_deck(color_identity=None, silent=False):
    commander = get_random_commander(color_identity=color_identity)
    color_identity = commander["color_identity"]
    cards = get_color_set(color_identity)
    nonlands = [commander["name"]]
    lands = []
    while len(nonlands) < 68:
        card = get_random_card(cards, silent=True)
        if "Land" in card["type_line"] and card not in lands:
            lands.append(card["name"])
            continue
        if card not in nonlands:
            nonlands.append(card["name"])
    deck = nonlands + lands
    return deck


def create_deckstring(deck):
    return "\n".join(str(i) for i in deck)


def save_deckfile(deckstring, name):
    filepath = f"{DIRECTORY}/../{name}.txt"
    with open(filepath, "w") as outfile:
        print(f"Writing to {filepath}...")
        outfile.write(deckstring)
        print("Successfully written to file.")


def main():
    """The main entrypoint to the program."""
    # fetch()
    # fetch_all_commanders()
    # initialize_all_color_sets()
    deck = generate_commander_deck()
    deck_name = clean_name(deck[0])
    save_deckfile(create_deckstring(deck), deck_name)


if __name__ == "__main__":
    main()
