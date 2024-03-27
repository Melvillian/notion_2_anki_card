from lib.intelligence import create_anki_cards_from_srs_blocks
from lib.notion_api import find_srs_blocks, mark_srs_block_as_processed
from lib.anki_utils import add_anki_card_to_deck


# This is the entrypoint to your program
def main():
    srs_blocks = find_srs_blocks()
    anki_cards = create_anki_cards_from_srs_blocks(srs_blocks)
    for card, block in iter(zip(anki_cards, srs_blocks)):
        add_anki_card_to_deck(card)
        mark_srs_block_as_processed(block)

    # user_provided_paragraph = "They are essentially enhanced juries for political problems, composed of a randomly chosen, demographically-representative group. They enable informed decisions on complex political questions. Over 700 instances worldwide have showcased their potential."
    # user_provided_topic = "Political Science and Law"
    # anki_card = generate_anki_cloze_card(user_provided_paragraph, user_provided_topic)
    # print(anki_card)


# This makes it so you can run `python main.py` to run this file
if __name__ == "__main__":
    main()
