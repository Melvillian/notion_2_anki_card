from pprint import pprint
from lib.intelligence import create_anki_cards_from_srs_blocks
from lib.notion_api import find_srs_blocks, mark_srs_block_as_processed
from lib.anki_utils import add_anki_card_to_deck, anki_call


# This is the entrypoint to your program
def main():
    srs_blocks = find_srs_blocks()
    anki_cards = create_anki_cards_from_srs_blocks(srs_blocks)
    for card in anki_cards:
        add_anki_card_to_deck(card)
        # mark_srs_block_as_processed(card.notion_block_id)


# This makes it so you can run `python main.py` to run this file
if __name__ == "__main__":
    main()
