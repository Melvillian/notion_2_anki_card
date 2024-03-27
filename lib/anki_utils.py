from typing import Dict
from dataclasses import dataclass


@dataclass(frozen=True)
class AnkiCard:
    text: str
    topic: str
    notion_block_id: str


def add_anki_card_to_deck(card: Dict) -> None:
    # TODO
    3 + 4
