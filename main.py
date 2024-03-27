from lib.intelligence import generate_anki_cloze_card
from lib.notion_api import find_srs_blocks
from pprint import pprint
from datetime import datetime, timedelta, timezone
from typing import Any


# This is the entrypoint to your program
def main():
    # get a list of all blocks edited in the last SEARCH_PERIOD_DAYS that contain un-processed
    # SRS-related blocks
    srs_blocks = find_srs_blocks()

    print("SRS BLOCKS")
    pprint(srs_blocks)

    # user_provided_paragraph = "They are essentially enhanced juries for political problems, composed of a randomly chosen, demographically-representative group. They enable informed decisions on complex political questions. Over 700 instances worldwide have showcased their potential."
    # user_provided_topic = "Political Science and Law"
    # anki_card = generate_anki_cloze_card(user_provided_paragraph, user_provided_topic)
    # print(anki_card)


# This makes it so you can run `python main.py` to run this file
if __name__ == "__main__":
    main()
