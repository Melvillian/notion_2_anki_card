from typing import Dict, Any
from dataclasses import dataclass
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

# This is the deck that you want to add cards to
DECK_NAME = os.environ["DECK_NAME"]


@dataclass(frozen=True)
class AnkiCard:
    text: str
    notion_block: Dict


def build_anki_connect_request(action, **params):
    """Simple helper function to build Anki Connect JSON requests"""
    return {"action": action, "params": params, "version": 6}


def anki_call(action: str, **params: Any) -> Dict:
    """Helper function to make Anki Connect API calls

    the `action` arguments can be found here: https://foosoft.net/projects/anki-connect/

    For example, to get all of the Anki Deck names and their ideas, you would write:
    `deck_and_ids = anki_call("deckNamesAndIds")`

    """
    request_json = json.dumps(build_anki_connect_request(action, **params))

    # We assume that Anki has been setup with the Anki Connect addon, and is
    # currently running
    response = requests.post("http://127.0.0.1:8765", data=request_json)
    response.raise_for_status()
    response_data = response.json()  # Parse JSON directly

    if len(response_data) != 2:
        raise Exception("response has an unexpected number of fields")
    if "error" not in response_data:
        raise Exception("response is missing required error field")
    if "result" not in response_data:
        raise Exception("response is missing required result field")
    if response_data["error"] is not None:
        raise Exception(response_data["error"])

    return response_data["result"]


def add_anki_card_to_deck(card: AnkiCard) -> None:
    """Adds an Anki card to the deck specified in the .env using Anki Connect"""
    note_params = {
        "deckName": DECK_NAME,
        "modelName": "Cloze",
        "fields": {"Text": card.text},
        "options": {
            "allowDuplicate": False,
            "duplicateScope": "deck",
            "duplicateScopeOptions": {
                "deckName": DECK_NAME,
                "checkChildren": False,
                "checkAllModels": False,
            },
        },
    }

    anki_call("addNote", note=note_params)
