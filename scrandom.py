import json
import os
import random
import re
import sys
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

import requests

if getattr(sys, "frozen", False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
application_path = Path(application_path)

REL_PATH = "output/bulk_data"
DIRECTORY = (application_path / REL_PATH).resolve()


def get_download_uri():
    print("Fetching download URI...")
    perma = "https://api.scryfall.com/bulk-data/oracle-cards"
    x = requests.get(perma).json()["download_uri"]
    print(f"Successfully fetched download URI: '{x}'")
    return x


def get_data(uri):
    print(f"Retrieving data from '{uri}'...")
    x = requests.get(uri).json()
    print(f"Successfully fetched data from '{uri}'.")
    return x


def write_to_json(data, name):
    today = datetime.today().strftime("%Y%m%d")
    filepath = f"{DIRECTORY}/{name}_{today}.json"
    print(f"Saving file to '{filepath}'...")
    with open(filepath, "w") as outfile:
        outfile.write(json.dumps(data))
    print(f"Successfully saved file to '{filepath}'.")


def open_json(filepath):
    with open(filepath) as infile:
        return json.load(infile)


def ensure_dir_exists():
    if not os.path.isdir(DIRECTORY):
        os.makedirs(DIRECTORY)


def is_file_old(file):
    today = datetime.today().strftime("%Y%m%d")
    return os.path.splitext(file.name)[0].split("_")[1] != today


def clear_old_files(force=False):
    ensure_dir_exists()
    with os.scandir(DIRECTORY) as it:
        for entry in it:
            if force:
                print(f"Force-removing {entry.name}")
                os.remove(entry)
            if is_file_old(entry):
                print(f"Removing old {entry.name}")
                os.remove(entry)


def paginate(uri):
    file = get_data(uri)
    total = file["total_cards"]
    all_data = []

    while True:
        all_data += [i for i in file["data"]]
        if "next_page" not in dict.keys(file):
            break
        time.sleep(0.1)
        file = get_data(file["next_page"])
    assert total == len(all_data)

    return all_data


def does_data_exist(filename):
    return filename in [i.name.split("_")[0] for i in os.scandir(DIRECTORY)]


def is_card_allowable(card):
    filters = [
        card["legalities"]["commander"] == "legal",
        "Attraction" not in card["type_line"],
        "Stickers" not in card["type_line"],
    ]
    return all(filters)


def fetch_oracle_cards():
    filename = "oracle-cards"
    if not does_data_exist(filename):
        uri = get_download_uri()
        data = [i for i in get_data(uri) if is_card_allowable(i)]
        write_to_json(data, filename)
    else:
        print(f"Data already exists: {filename}")


def fetch_all_commanders():
    filename = "all-commanders"
    if not does_data_exist(filename):
        query = "q=is%3Acommander+legal%3Acommander"
        uri = "https://api.scryfall.com/cards/search?" + query
        data = [i for i in paginate(uri) if is_card_allowable(i)]
        write_to_json(data, filename)
    else:
        print(f"Data already exists: {filename}")


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


def equal_color_id(card, match):
    return set(card["color_identity"]) == set(match)


def within_color_id(card, match):
    return set(card["color_identity"]) <= set(match)


def get_random_commander(color_id=None):
    filename = get_file_name("all-commanders")
    filepath = f"{DIRECTORY}/{filename}"
    cards = open_json(filepath)
    if color_id is not None:
        cards = [i for i in cards if equal_color_id(i, color_id)]
    return random.choice(cards)


def get_color_set(color_id):
    filename = get_file_name("oracle-cards")
    filepath = f"{DIRECTORY}/{filename}"
    cards = open_json(filepath)
    cards = [i for i in cards if within_color_id(i, color_id)]
    return cards


def get_random_card(cards):
    return random.choice(cards)


def generate_commander_deck(color_id=None, commander=None, silent=True):
    if commander is None:
        commander = get_random_commander(color_id=color_id)
    deck_add_message("Commander", commander["name"])
    color_id = commander["color_identity"]
    cards = get_color_set(color_id)
    nonlands = [commander["name"]]
    lands = []
    while len(nonlands) < 62:
        card = get_random_card(cards)
        if card["name"] in nonlands or card["name"] in lands:
            continue
        if not silent:
            short_type = card["type_line"].split("—")[0].strip()
            deck_add_message(short_type, card["name"])
        if "Land" in card["type_line"]:
            lands.append(card["name"])
            continue
        nonlands.append(card["name"])
    deck = nonlands + lands
    return deck


def create_deckstring(deck):
    return "\n".join(str(i) for i in deck)


def create_moxfield_link(deck):
    link = "https://www.moxfield.com/import?c="
    link += urllib.parse.quote_plus(create_deckstring(deck))
    return link


def save_deckfile(deck, name):
    filepath = (DIRECTORY / f"../{name}.txt").resolve()
    deckstring = create_deckstring(deck)
    with open(filepath, "w") as outfile:
        print(f"Writing to {filepath}...")
        outfile.write(deckstring)
        print("Successfully written to file.")


def initialize(force=False):
    clear_old_files(force)
    fetch_oracle_cards()
    fetch_all_commanders()


def main():
    """The main entrypoint to the program."""
    initialize()
    deck = generate_commander_deck(silent=True)
    deck_name = clean_name(deck[0])
    save_deckfile(deck, deck_name)
    # print(create_moxfield_link(deck))


if __name__ == "__main__":
    main()
