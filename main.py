import argparse

from lib.intelligence import create_anki_cards_from_srs_blocks
from lib.notion_api import find_srs_blocks, mark_srs_block_as_processed
from lib.anki_utils import add_anki_card_to_deck, anki_call


# This is the entrypoint to your program
def main():
    parser = setup_cli_parsers()
    args = parser.parse_args()

    if args.command:
        args.func()
    else:
        parser.print_help()

    return

    srs_blocks = find_srs_blocks()
    anki_cards = create_anki_cards_from_srs_blocks(srs_blocks)
    assert len(anki_cards) == len(srs_blocks)

    for block, card in list(zip(srs_blocks, anki_cards)):
        add_anki_card_to_deck(card)
        mark_srs_block_as_processed(block)


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
    generate_cards_parser.set_defaults(func=add_anki_card_and_mark_as_processed)

    return parser


def find_srs_blocks_and_create_anki_cards():
    print("find_srs_blocks_and_create_anki_cards")


def add_anki_card_and_mark_as_processed():
    print("add_anki_card_and_mark_as_processed")


# This makes it so you can run `python main.py` to run this file
if __name__ == "__main__":
    main()
