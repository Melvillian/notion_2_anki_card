from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

# note: the API token gets automatically pulled in from the .env by the OpenAI class
client = OpenAI()

system_prompt_card_generation_template = """
You are a flashcard creation expert. Your task is to analyze the paragraph that comes after the “**Input Paragraph:**” prefix provided by the user, as well as a user-provided Topic that is from one of the 10 topics below, and generate a single Anki cloze deletion flashcard that challenges deeper understanding. You must prioritize these guidelines:

- **Information Density:** Choose a segment of the user-provided paragraph that contains a key fact, definition, or important concept relevant to the topic.
- **Conciseness:** The cloze deletion should be as short as possible while still providing enough context for recall.
- **Deeper Understanding:** The card should test more than simple memorization. If possible, structure the cloze to require analysis, comparison, or application of the concept.

The 10 topics are: World History, Science and Technology, Geography and Cultures, Arts and Literature, Biology and Medicine, Environmental Science and Ecology, Philosophy and Religion, Economics and Business, Political Science and Law, Mathematics and Physics

For example, given the following input enclosed by double-quotes:

"
**Input Paragraph:** In the field of energy economics, the time-to-start for different power plants is an important factor in determining the optimal mix of energy sources. Power plants that can be started quickly, such as natural gas-fired plants which take 10 minutes to start, are better suited to handle fluctuations in demand than plants that take longer to start.
**Topic:** Economics and Business
"
Then the output should look like the following valid Python string:

"A natural gas plant takes about {{c1::10 minutes}} to start"
"""

user_prompt_card_generation_template = """
**Input Paragraph:** {paragraph}
**Topic:** {topic}
"""


def generate_anki_cloze_card(paragraph, topic, model_version="gpt-3.5-turbo"):
    """Generate an Anki cloze deletion flashcard from input paragraph and topic"""

    user_prompt_content = user_prompt_card_generation_template.format(
        paragraph=paragraph, topic=topic
    )

    completion = client.chat.completions.create(
        model=model_version,
        messages=[
            {
                "role": "system",
                "content": system_prompt_card_generation_template,
            },
            {
                "role": "user",
                "content": user_prompt_content,
            },
        ],
    )

    # TODO: do proper error handling
    return completion.choices[0].message
