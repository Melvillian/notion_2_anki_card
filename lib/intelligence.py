from openai import OpenAI
import re
import os
from dotenv import load_dotenv
from typing import List, Dict
from .notion_api import MENTION_TEXT
from .anki_utils import AnkiCard

load_dotenv()  # take environment variables from .env.

# note: the API token gets automatically pulled in from the .env by the OpenAI class
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Text categories that help the anki card generation prompt hone in on a
# particular category of ideas
# TODO: evaluate if this actually helps with the prompt. If it doesn't help
# then we should remove so that it doesn't unnecessarily increase the cost
# of the prompt
TOPICS = [
    "World History",
    "Science and Technology",
    "Geography and Cultures",
    "Arts and Literature",
    "Biology and Medicine",
    "Environmental Science and Ecology",
    "Philosophy and Religion",
    "Economics and Business",
    "Political Science and Law",
    "Mathematics and Physics",
]

MODEL_VERSION = "gpt-3.5-turbo"

SYSTEM_PROMPT_CARD_GENERATION_TEMPLATE = """
You are a flashcard creation expert. Your task is to analyze the paragraph that comes after the “**Input Paragraph:**” prefix provided by the user, as well as a user-provided Topic that is from one of the 10 topics below, and generate a single Anki cloze deletion flashcard that challenges deeper understanding. You must prioritize these guidelines:

- **Information Density:** Choose a segment of the user-provided paragraph that contains a key fact, definition, or important concept relevant to the topic.  
- **Conciseness:** The cloze deletion should be as short as possible while still providing enough context for recall.
- **Deeper Understanding:** The card should test more than simple memorization. If possible, structure the cloze to require analysis, comparison, or application of the concept.

The 10 topics are: {topics}

For example, given the following input:

**Input Paragraph:** In the field of energy economics, the time-to-start for different power plants is an important factor in determining the optimal mix of energy sources. Power plants that can be started quickly, such as natural gas-fired plants which take 10 minutes to start, are better suited to handle fluctuations in demand than plants that take longer to start.  
**Topic:** Economics and Business

Then the output should look like the following valid Python string:  

A natural gas plant takes about {{c1::10 minutes}} to start
"""

USER_PROMPT_CARD_GENERATION_TEMPLATE = """
**Input Paragraph:** {text}
**Topic:** {topic}
"""

SYSTEM_TOPIC_SELECTION_PROMPT_TEMPLATE = """
Your purpose is to categorize text into exactly 1 of the following topics, given as a comma-separated list of 10 topics. You MUST respond with a topic that is one of the 10 options provided below:

{topics}
"""

USER_TOPIC_SELECTION_PROMPT_TEMPLATE = """
Please categorize the following text:

{text}
"""


def generate_anki_cloze_card(text: str, topic) -> str:
    """Generate an Anki cloze deletion flashcard from input text and topic"""

    system_prompt = SYSTEM_PROMPT_CARD_GENERATION_TEMPLATE.format(
        topics=", ".join(TOPICS)
    )
    user_prompt = USER_PROMPT_CARD_GENERATION_TEMPLATE.format(text=text, topic=topic)

    completion = client.chat.completions.create(
        model=MODEL_VERSION,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    # TODO: do proper error handling
    return completion.choices[0].message.content


def create_anki_cards_from_srs_blocks(srs_blocks: List[Dict]) -> List[AnkiCard]:
    """Given a list of raw Notion blocks that contain mentions, generate Anki cloze cards from them"""
    anki_cards: List[AnkiCard] = []

    for block in srs_blocks:
        # a Notion block consists of a list of section dicts which contain the
        # actual text in the "plain_text" key entry. Here we reconstitute
        # the block's full text from the sections, while ignoring the MENTION tag
        # because it's irrelevant to Anki card generation
        srs_item_text = "".join(
            [
                section["plain_text"]
                for section in block.get(block["type"], {}).get("rich_text", [])
                if MENTION_TEXT not in section["plain_text"]
            ]
        )

        # create the text we'll put in the Anki card using an LLM
        topic = get_topic_from_text(srs_item_text)
        anki_card_text = generate_anki_cloze_card(srs_item_text, topic)
        validated_anki_card_text = validate_and_fix_card_text(anki_card_text)

        # add the Anki Card to our total list of cards we'll later
        # add to our Anki Deck
        anki_card = AnkiCard(validated_anki_card_text, block)
        anki_cards.append(anki_card)

    return anki_cards


def validate_and_fix_card_text(anki_card_text: str) -> str:
    """Validate Anki card text and fix any issues, returning the fixed text"""

    # GPT-3.5 likes to surround its output in double-quotes
    # so we strip those here
    if anki_card_text[0] == '"':
        anki_card_text = anki_card_text[1:]
    if anki_card_text[-1] == '"':
        anki_card_text = anki_card_text[:-1]

    anki_card_text = make_double_curly(anki_card_text)

    return anki_card_text


def make_double_curly(text):
    """
    Simple helper function to correct GPT-3's habit of using
    single curly braces when it should use double curly braces
    """

    def replace_single(match):
        return "{{" + match.group(1) + "}}"

    return re.sub(r"\{(.*?)\}", replace_single, text)


def get_topic_from_text(srs_item_text: str) -> str:
    """Use an LLM API to categorize text into one of the predefined topics given in TOPICS"""

    system_prompt = SYSTEM_TOPIC_SELECTION_PROMPT_TEMPLATE.format(
        topics=", ".join(TOPICS)
    )

    user_prompt = USER_TOPIC_SELECTION_PROMPT_TEMPLATE.format(text=srs_item_text)

    completion = client.chat.completions.create(
        model=MODEL_VERSION,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
    )

    # TODO: do proper error handling
    topic = completion.choices[0].message.content
    if topic not in TOPICS:
        raise ValueError(
            f"Topic {topic} is not a valid option. Must be one of {TOPICS}"
        )
    return topic
