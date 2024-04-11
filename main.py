import argparse
import pickle
import sys
from typing import List
from lib.intelligence import create_anki_cards_from_srs_blocks
from lib.notion_api import find_srs_blocks, mark_srs_block_as_processed
from lib.anki_utils import add_anki_card_to_deck, AnkiCard


# This is the entrypoint to your program
def main():
    """run either the script to grab text from notion, use an LLM to create card text,
    and then save it to a file for later acceptance by the user, or run the CLI acceptance
    tool to take text, generate an Anki Card, and add it to the Deck"""
    parser = setup_cli_parsers()
    args = parser.parse_args()

    if args.command:
        args.func()
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
    scan_notion_parser.set_defaults(func=find_srs_blocks_and_create_anki_cards)

    generate_cards_parser = subparsers.add_parser(
        "generate_cards",
        help="Generate Anki cards from suggested cards stored in ./notion_2_anki_card/out/cards.json",
    )
    generate_cards_parser.set_defaults(func=generate_anki_card_and_mark_as_processed)

    return parser


def find_srs_blocks_and_create_anki_cards():
    print("find_srs_blocks_and_create_anki_cards")
    srs_blocks = find_srs_blocks()
    anki_cards = create_anki_cards_from_srs_blocks(srs_blocks)

    assert len(anki_cards) == len(srs_blocks)
    write_anki_cards_to_pickle_file(anki_cards)


def write_anki_cards_to_pickle_file(anki_cards: List[AnkiCard]):
    """Write the generated Anki cards to a pickle file for later use"""
    # first, see if we have any existing saved potential card text from a prior
    # execution of the script
    existing_cards = []
    try:
        with open("notion_2_anki_card/out/cards.pkl", "rb") as f:
            existing_cards = pickle.load(f)
    except FileNotFoundError:
        existing_cards.extend(anki_cards)

    # now, save all the card text to the file
    with open("notion_2_anki_card/out/cards.pkl", "wb") as f:
        pickle.dump(existing_cards, f)

    print("Wrote Anki cards to notion_2_anki_card/out/cards.pkl")


def generate_anki_card_and_mark_as_processed():
    existing_cards = []
    try:
        with open("notion_2_anki_card/out/cards.pkl", "rb") as f:
            existing_cards = pickle.load(f)
    except FileNotFoundError:
        print("No existing cards found, Aborting...")
        sys.exit(0)
    for card in existing_cards:
        add_anki_card_to_deck(card)
        mark_srs_block_as_processed(card.block)


# This makes it so you can run `python main.py` to run this file
if __name__ == "__main__":
    main()
