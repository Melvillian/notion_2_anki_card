import argparse
import pickle
import os
from typing import List
from lib.intelligence import create_anki_cards_from_srs_blocks
from lib.notion_api import find_srs_blocks, mark_srs_block_as_processed
from lib.anki_utils import AnkiCard, add_anki_card_to_deck

# default filepath at which we store the inference card text
CARD_FILEPATH = "out/cards.pkl"


# This is the entrypoint to your program
def main():
    """run either the script to grab text from notion, use an LLM to create card text,
    and then save it to a file for later acceptance by the user, or run the CLI acceptance
    tool to take text, generate an Anki Card, and add it to the Deck"""
    parser = setup_cli_parsers()
    args = parser.parse_args()

    if not args.pickle_filepath.endswith(".pkl"):
        raise ValueError("--pickle-filepath must end with .pkl, e.g. 'out/cards.pkl'")

    if args.command == "scan_notion":
        find_srs_blocks_and_create_anki_cards(args.pickle_filepath)
    elif args.command == "generate_cards":
        generate_anki_card_and_mark_as_processed(args.pickle_filepath)
    else:
        parser.print_help()
    return


def setup_cli_parsers():
    parser = argparse.ArgumentParser(
        description="Convert Notion SRS blocks to Anki cards"
    )
    subparsers = parser.add_subparsers(help="commands", dest="command")

    scan_notion_parser = subparsers.add_parser(
        "scan_notion", help="Scan Notion for new SRS blocks and add them to Anki"
    )
    scan_notion_parser.add_argument(
        "--pickle-filepath",
        type=str,
        default=CARD_FILEPATH,
        help=f"The filepath of the *.pkl that stores the Anki text that will later be used in `generate_cards`. Defaults to ./{CARD_FILEPATH}",
    )

    generate_cards_parser = subparsers.add_parser(
        "generate_cards",
        help="Add cards to your Anki deck using the text from the pickle file generated by `scan_notion`",
    )
    generate_cards_parser.add_argument(
        "--pickle-filepath",
        type=str,
        default=CARD_FILEPATH,
        help=f"The filepath of the *.pkl file we'll read Anki text from, generated by the scan_notion command. Defaults to ./{CARD_FILEPATH}",
    )

    return parser


def find_srs_blocks_and_create_anki_cards(pickle_filepath: str):
    srs_blocks = find_srs_blocks()
    anki_cards = create_anki_cards_from_srs_blocks(srs_blocks)

    assert len(anki_cards) == len(srs_blocks)
    write_anki_cards_to_pickle_file(anki_cards, pickle_filepath)


def write_anki_cards_to_pickle_file(anki_cards: List[AnkiCard], pickle_filepath: str):
    """Write the generated Anki cards to a pickle file for later use"""
    if len(anki_cards) == 0:
        print("No card text found from Notion, shutting down...")
        return

    # first, see if we have any existing saved potential card text from a prior
    # execution of the script
    existing_cards = []
    try:
        with open(pickle_filepath, "rb") as f:
            existing_cards = pickle.load(f)
            existing_cards.extend(anki_cards)
    except FileNotFoundError:
        existing_cards.extend(anki_cards)

    # filter out any duplicates, which will happen if we run the scan_notion
    # command twice without running the generate_cards command in between
    unique_cards: List[AnkiCard] = []
    for card in existing_cards:
        block_id = card.notion_block["id"]
        num_card = len(
            [
                another_card
                for another_card in unique_cards
                if another_card.notion_block["id"] == block_id
            ]
        )
        if num_card == 0:
            unique_cards.append(card)
        elif num_card > 1:
            print("something wierd happened...")
    if len(unique_cards) == 0:
        print("No new cards found, shutting down...")
        return

    # now, save all the card text to the file
    with open(pickle_filepath, "wb") as f:
        pickle.dump(unique_cards, f)

    plural_or_singular_cards = "card" if len(unique_cards) == 1 else "cards"
    print(
        f"Wrote {len(unique_cards)} Anki {plural_or_singular_cards} to {pickle_filepath}"
    )


def generate_anki_card_and_mark_as_processed(pickle_filepath: str):
    existing_cards = []
    try:
        with open(pickle_filepath, "rb") as f:
            existing_cards = pickle.load(f)
    except FileNotFoundError:
        print("No existing cards found, shutting down...")
        return
    print("Please view the list of cards to create and either accept or deny each...\n")
    for card in existing_cards:
        print("")
        print(card.text)
        user_input = input("Do you want to generate this card? (y/n): ").strip().lower()
        if user_input == "y" or user_input == "":
            notion_block_id = card.notion_block["id"]
            print(f"adding card with id {notion_block_id} to Anki deck...")
            add_anki_card_to_deck(card)
        print(f"Updating block with ID: {card.notion_block['id']}")
        mark_srs_block_as_processed(card.notion_block)

    print(f"deleting {pickle_filepath}")
    os.remove(pickle_filepath)


# This makes it so you can run `python main.py` to run this file
if __name__ == "__main__":
    main()
