import fetch_bulk_data as bulk
import os
import re
import random

from pathlib import Path

MOD_PATH = Path(__file__).parent
REL_PATH = "../output/bulk_data"
DIRECTORY = (MOD_PATH / REL_PATH).resolve()


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
    commanders = bulk.open_json(filepath)
    if color_identity is not None:
        commanders = [
            i for i in commanders if set(i["color_identity"]) == set(color_identity)
        ]
    x = random.choice(commanders)
    if not silent:
        deck_add_message("COMMANDER", x["name"])
    return x


def identity_to_color_string(color_identity):
    color_string = "colorless"
    for i in color_identity:
        color_string += f"-{i}"
    return color_string


def get_color_set(color_identity):
    color_string = identity_to_color_string(color_identity)

    filename = get_file_name(color_string)
    # Test if color-file already exists and read it
    if filename is not None:
        print(f"{filename} already exists, moving on...")
        filepath = f"{DIRECTORY}/{filename}"
        return bulk.open_json(filepath)
    # Otherwise create a new color-file
    filename = get_file_name("oracle-cards")
    filepath = f"{DIRECTORY}/{filename}"
    cards = bulk.open_json(filepath)
    cards = [
        i
        for i in cards
        if set(i["color_identity"]) <= set(color_identity)
        and i["legalities"]["commander"] == "legal"
    ]
    bulk.write_to_json(cards, color_string)
    return cards


def initialize_all_color_sets():
    filename = get_file_name("oracle-cards")
    filepath = f"{DIRECTORY}/{filename}"
    cards = bulk.open_json(filepath)
    color_set_list = set([tuple(i["color_identity"]) for i in cards])
    for i in color_set_list:
        get_color_set(i)
    print("Finished initializing all color sets.")


def get_random_card(cards, silent=False):
    x = random.choice(cards)
    typex = x["type_line"].split("—")[0].strip()
    if not silent:
        deck_add_message(typex, x["name"])
    return x


def main():
    """The main entrypoint to the program."""
    # bulk.fetch()
    # bulk.fetch_all_commanders()
    # initialize_all_color_sets()
    commander = get_random_commander()
    color_identity = commander["color_identity"]
    cards = get_color_set(color_identity)
    nonlands = [commander["name"]]
    lands = []
    while len(nonlands) < 68:
        card = get_random_card(cards)
        if "Land" in card["type_line"] and card not in lands:
            lands.append(card["name"])
            continue
        if card not in nonlands:
            nonlands.append(card["name"])
    deck = nonlands + lands
    deck_name = clean_name(commander["name"])
    with open(f"{DIRECTORY}/../{deck_name}.txt", "w") as outfile:
        print("Writing to file...")
        outfile.write("\n".join(str(i) for i in deck))
        print("Successfully written to file.")


if __name__ == "__main__":
    main()
