import asyncio
import aiohttp
from aioscryfall.client import ScryfallClient
from pathlib import Path

MOD_PATH = Path(__file__).parent
REL_PATH = "../output"
DIRECTORY = (MOD_PATH / REL_PATH).resolve()
NONLAND = 68
DEFAULT_FILTERS = [
    "legal:commander",
    "-t:basic",
]
UNF_FILTERS = [
    "-o:sticker",
    '-o:"an attraction"',
    '-o:"target attraction"',
    "-o:attraction",
    "-t:attraction",
    "-o:{TK}",
]


def deck_add_message(card_type, name):
    print(f'{card_type}:\tAdding "{name}" to your deck...')


async def get_random_commander(color_identity=None, silent=False):
    async with aiohttp.ClientSession() as session:
        client = ScryfallClient(session)
        q_string = " ".join(DEFAULT_FILTERS + UNF_FILTERS) + " is:commander"
        if color_identity is not None:
            q_string += f"color={color_identity}"
        x = await client.cards.random(query=q_string)
        if not silent:
            deck_add_message("COMMANDER", x.name)
        return x


async def get_random_card(color_identity, silent=False):
    async with aiohttp.ClientSession() as session:
        client = ScryfallClient(session)
        q_string = (
            " ".join(DEFAULT_FILTERS + UNF_FILTERS) + f" commander:{color_identity}"
        )
        x = await client.cards.random(query=q_string)
        typex = x.type_line.split("—")[0].strip()
        if not silent:
            deck_add_message(typex, x.name)
        return x


async def main():
    commander = await get_random_commander()
    commander_identity = "".join(["" + c for c in commander.color_identity])
    print(f"Color identity is {commander_identity}")
    q_string = (
        " ".join(DEFAULT_FILTERS + UNF_FILTERS) + f" commander:{commander_identity}"
    )
    print(f"Searching using query ({q_string})...")
    nonlands = []
    lands = []
    nonlands.append(commander.name)
    while len(nonlands) < NONLAND:
        x = await get_random_card(commander_identity)
        if "Land" in x.type_line and x.name not in lands:
            lands.append(x.name)
            continue
        if x.name not in nonlands:
            nonlands.append(x.name)
    deck = nonlands + lands
    safe_commander_name = commander.name.replace(" // ","|").replace(" ","-")
    with open(f"{DIRECTORY}/output.txt", "w") as outfile:
        print("Writing to file...")
        outfile.write("\n".join(str(i) for i in deck))
        print("Successfully written to file.")


if __name__ == "__main__":
    asyncio.run(main())
