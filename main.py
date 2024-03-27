from lib.intelligence import generate_anki_cloze_card
from lib.notion_api import find_srs_blocks
from pprint import pprint
from datetime import datetime, timedelta
from typing import Any

# Only search through the last SEARCH_PERIOD_DAYS days of recently edited pages.
# I plan to run this in a cronjob daily so we won't need to iterate over many
# pages
SEARCH_PERIOD_DAYS = 7


# This is the entrypoint to your program
def main():

    now = datetime.now()
    end_date = now - timedelta(days=SEARCH_PERIOD_DAYS)

    print(f"END DATE: {end_date}")

    # get a list of all blocks edited in the last SEARCH_PERIOD_DAYS that contain un-processed
    # SRS-related blocks

    srs_blocks = find_srs_blocks()

    # user_provided_paragraph = "They are essentially enhanced juries for political problems, composed of a randomly chosen, demographically-representative group. They enable informed decisions on complex political questions. Over 700 instances worldwide have showcased their potential."
    # user_provided_topic = "Political Science and Law"
    # anki_card = generate_anki_cloze_card(user_provided_paragraph, user_provided_topic)
    # print(anki_card)


# This makes it so you can run `python main.py` to run this file
if __name__ == "__main__":
    main()
