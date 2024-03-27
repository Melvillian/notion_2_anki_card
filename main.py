from lib.intelligence import generate_anki_cloze_card
from lib.notion_api import get_descending_pages_generator
from pprint import pprint
from datetime import datetime, timedelta

SEARCH_PERIOD_DAYS = 30


# This is the entrypoint to your program
def main():

    now = datetime.now()
    end_date = now - timedelta(days=SEARCH_PERIOD_DAYS)

    # search for pages that were edited in the last SEARCH_PERIOD_DAYS looking for matches to the given keywords

    for page in get_descending_pages_generator():
        if end_date > datetime.fromisoformat(page["last_edited_time"]):
            break

        print("\n\n\n\nWE FOUND ONE")
        pprint(page)
    # user_provided_paragraph = "They are essentially enhanced juries for political problems, composed of a randomly chosen, demographically-representative group. They enable informed decisions on complex political questions. Over 700 instances worldwide have showcased their potential."
    # user_provided_topic = "Political Science and Law"
    # anki_card = generate_anki_cloze_card(user_provided_paragraph, user_provided_topic)
    # print(anki_card)


# This makes it so you can run `python main.py` to run this file
if __name__ == "__main__":
    main()
