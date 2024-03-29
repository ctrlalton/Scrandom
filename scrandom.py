"""Generate random EDH decklists."""
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
OUTPUT = (Path(application_path) / "output/").resolve()
BULK_DATA = (OUTPUT / "bulk_data").resolve()


class Card:
    """Store card info from scryfall"""

    def __init__(self, data: list):
        self.data = data
        self.cid = set(data["color_identity"])

    def __getitem__(self, index: int):
        return self.data[index]

    def __str__(self):
        return self["name"]


class Deck:
    """Store a list of card objects"""

    def __init__(self, data=None):
        if data is None:
            self.data = []
        self.data = data

    def _is_valid_operand(self, other):
        return isinstance(other, (Deck, Card))

    def __getitem__(self, index: int) -> Card:
        return self.data[index]

    def __setitem__(self, index: int, value: Card):
        self.data[index] = value

    def append(self, value):
        """Implement list append function"""
        self.data.append(value)

    def __len__(self):
        return len(self.data)

    def __str__(self):
        return "\n".join(str(i) for i in self.data)

    def __add__(self, other):
        if not self._is_valid_operand(other):
            return NotImplemented
        if isinstance(other, Card):
            return Deck(self.data + [other])
        return Deck(self.data + other.data)


def get_download_uri():
    """Fetch download URI from permalink"""
    print("Fetching download URI...")
    perma = "https://api.scryfall.com/bulk-data/oracle-cards"
    x = requests.get(perma, timeout=10).json()["download_uri"]
    print(f"Successfully fetched download URI: '{x}'")
    return x


def get_data(uri):
    """Request data from provided uri"""
    print(f"Retrieving data from '{uri}'...")
    x = requests.get(uri, timeout=10).json()
    print(f"Successfully fetched data from '{uri}'.")
    return x


def write_to_json(data, name):
    """Write data to json with formatted name"""
    today = datetime.today().strftime("%Y%m%d")
    filepath = f"{BULK_DATA}/{name}_{today}.json"
    print(f"Saving file to '{filepath}'...")
    with open(filepath, "w", encoding="utf8") as outfile:
        outfile.write(json.dumps(data))
    print(f"Successfully saved file to '{filepath}'.")


def open_json(filepath):
    """Open a json from path"""
    with open(filepath, "r", encoding="utf8") as infile:
        return json.load(infile)


def ensure_dir_exists():
    """Create a directory if not exists"""
    if not os.path.isdir(BULK_DATA):
        os.makedirs(BULK_DATA)


def is_file_old(file):
    """Test if filename is not from today"""
    today = datetime.today().strftime("%Y%m%d")
    return os.path.splitext(file.name)[0].split("_")[1] != today


def clear_old_files(force=False):
    """Remove old files"""
    ensure_dir_exists()
    with os.scandir(BULK_DATA) as it:
        for entry in it:
            if force:
                print(f"Force-removing {entry.name}")
                os.remove(entry)
            if is_file_old(entry):
                print(f"Removing old {entry.name}")
                os.remove(entry)


def paginate(uri):
    """Extract all data from provided uri if it is across multiple pages"""
    file = get_data(uri)
    total = file["total_cards"]
    all_data = []

    while True:
        all_data += list(file["data"])
        if "next_page" not in dict.keys(file):
            break
        time.sleep(0.1)
        file = get_data(file["next_page"])
    assert total == len(all_data)

    return all_data


def does_data_exist(filename):
    """Look for the provided filename in the directory"""
    return filename in [i.name.split("_")[0] for i in os.scandir(BULK_DATA)]


def is_card_allowable(card: Card) -> bool:
    """Check if a card meets playability requirement"""
    filters = [
        card["legalities"]["commander"] == "legal",
        "Attraction" not in card["type_line"],
        "Stickers" not in card["type_line"],
    ]
    return all(filters)


def fetch_oracle_cards():
    """Download all card data for legal cards"""
    filename = "oracle-cards"
    if not does_data_exist(filename):
        uri = get_download_uri()
        data = [i for i in get_data(uri) if is_card_allowable(i)]
        write_to_json(data, filename)
    else:
        print(f"Data already exists: {filename}")


def fetch_all_commanders():
    """Download all card data for legal commanders"""
    filename = "all-commanders"
    if not does_data_exist(filename):
        query = "q=is%3Acommander+legal%3Acommander"
        uri = "https://api.scryfall.com/cards/search?" + query
        data = [i for i in paginate(uri) if is_card_allowable(i)]
        write_to_json(data, filename)
    else:
        print(f"Data already exists: {filename}")


def get_file_name(name):
    """Get actual filename from prefix (without date)"""
    with os.scandir(BULK_DATA) as it:
        for entry in it:
            if entry.name.split("_")[0] == name:
                return entry.name
    return None


def clean_name(name: str) -> str:
    """Format cardname in filename friendly format"""
    name = re.sub(
        "[.,'<>:\"/\\|?*]",
        "",
        str(name)
        .replace(" // ", "_")
        .replace(" ", "_")
        .replace("-", "_")
        .replace("&", "and"),
    )
    return name


def deck_add_message(card):
    """Print an output string when a card is added"""
    print(f'Adding "{card["name"]}" to your deck...'.expandtabs(25))


def get_random_commander(color_id: set[str] = None) -> Card:
    """Select a random commander (optional color choice)"""
    filename = get_file_name("all-commanders")
    filepath = f"{BULK_DATA}/{filename}"
    cards = list(map(Card, open_json(filepath)))
    if color_id is not None:
        cards = [i for i in cards if i.cid == color_id]
    return random.choice(cards)


def get_color_set(color_id: set[str]) -> list[Card]:
    """Returns list of cards within a color identity"""
    filename = get_file_name("oracle-cards")
    filepath = f"{BULK_DATA}/{filename}"
    cards = list(map(Card, open_json(filepath)))
    cards = [i for i in cards if i.cid <= color_id]
    return cards


def get_random_card(cards: list[Card]) -> Card:
    """Picks a random card from the list provided"""
    return random.choice(cards)


def generate_commander_deck(
    color_id: set[str] = None,
    commander: Card = None,
    silent: bool = True,
) -> Deck:
    """Generate a random commander deck"""
    if commander is None:
        commander = get_random_commander(color_id=color_id)
    if not silent:
        deck_add_message(commander)
    cards = get_color_set(commander.cid)
    nonlands = Deck([commander["name"]])
    lands = Deck()
    while len(nonlands) < 62:
        card = get_random_card(cards)
        if card in nonlands + lands:
            continue
        if not silent:
            deck_add_message(card)
        if "Land" in card["type_line"]:
            lands += card
        else:
            nonlands += card
    return nonlands + lands


def create_moxfield_link(deck: Deck) -> str:
    """Return a link to import deck into Moxfield"""
    link = "https://www.moxfield.com/import?c="
    link += urllib.parse.quote_plus(str(deck))
    return link


def save_deckfile(deck: Deck, name: str):
    """Save the deck to a file containing commander name"""
    filepath = f"{OUTPUT}/{name}.txt"
    with open(filepath, "w", encoding="utf8") as outfile:
        print(f"Writing to {filepath}...")
        outfile.write(str(deck))
        print("Successfully written to file.")


def initialize(force=False):
    """Setup files and fetch necessary data"""
    clear_old_files(force)
    fetch_oracle_cards()
    fetch_all_commanders()


def main():
    """The main entrypoint to the program."""
    initialize()
    deck = generate_commander_deck()
    deck_name = clean_name(deck[0])
    save_deckfile(deck, deck_name)
    # print(create_moxfield_link(deck))


if __name__ == "__main__":
    main()
