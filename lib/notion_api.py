import os
import json
import sys
from dotenv import load_dotenv
from .http_utils import get, post, patch
from typing import Any, Tuple, List, Dict
from notion_client import Client
import logging
import structlog
from notion_client.helpers import iterate_paginated_api
from datetime import datetime, timedelta, timezone
from pprint import pprint

load_dotenv()

logger = structlog.wrap_logger(
    logging.getLogger("notion-client"),
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)

notion = Client(auth=os.environ["NOTION_KEY"], logger=logger, log_level=logging.DEBUG)

# This is the Notion mention text that I will include in a Notion block in order
# to signal that I want the surounding block of text to be used to generate
# an Anki card
MENTION_TEXT = "srs-item"

# Only search through the last SEARCH_PERIOD_DAYS days of recently edited pages.
# I plan to run this in a cronjob daily so we won't need to iterate over many
# pages
SEARCH_PERIOD_DAYS = 1

# These are all of the Notion block types that we want to recurse through,
# looking for more Notion blocks. For instance, we want to ignore the
# "callout" block type, because I never write further nested
# blocks within a callout.
BLOCK_TYPES_TO_PROCESS = [
    "paragraph",
    "bulleted_list_item",
    "heading_1",
    "heading_2",
    "heading_3",
    "numbered_list_item",
    "toggle",
]


def find_srs_blocks():
    """

    Based on the Notion API key you're using and the pages that have been
    shared with the key's integration, search through recently-edited pages
    in descending order looking for Notion blocks that have the @srs-item
    tag in them, and generate anki cards from the information in that block
    """

    # only search a subset of the pages in order to save on time and compute
    now = datetime.now(timezone.utc)
    end_date = now - timedelta(days=SEARCH_PERIOD_DAYS)
    print(f"END DATE: {end_date}")

    srs_blocks = []

    for page_chunk in iterate_paginated_api(
        notion.search,
        sort={"direction": "descending", "timestamp": "last_edited_time"},
        filter={"value": "page", "property": "object"},
    ):
        # the bulk of this script's work happens here
        (some_srs_blocks, should_break) = find_srs_blocks_in_chunk(page_chunk, end_date)
        srs_blocks.extend(some_srs_blocks)
        if should_break:
            break

    print("SRS BLOCKS")
    pprint(srs_blocks)
    return srs_blocks


def find_srs_blocks_in_chunk(page_chunk, end_date: datetime) -> Tuple[list, bool]:
    """
    Returns a tuple with:
        - A list of SRS blocks found in the page chunk
        - A boolean indicating if we should stop iterating further pages

    We don't want to waste time and compute on iterating through pages that
    are too old. This function returns True if we should stop iterating
    further pages.

    For debugging purposes, here is an example of what a `page_chunk` looks
    like:

    ```json
    [
    {
        'archived': False,
        'cover': None,
        'created_by': {'id': '5be127e8-c6d7-4a7b-a46d-a0eb3bc9d6af',
                    'object': 'user'},
        'created_time': '2024-03-26T10:58:00.000Z',
        'icon': None,
        'id': 'aab9a1b4-a9ff-4415-a674-0a3151ba8a76',
        'last_edited_by': {'id': '5be127e8-c6d7-4a7b-a46d-a0eb3bc9d6af',                                                                                                                                     07:34:16 [2788/3839]
                        'object': 'user'},
        'last_edited_time': '2024-03-26T18:55:00.000Z',
        'object': 'page',
        'parent': {'page_id': '7b1b3b0c-14cb-45a6-a4b6-d2b48faecccb',
                'type': 'page_id'},
        'properties': {'title': {'id': 'title',
                                'title': [{'annotations': {'bold': False,
                                                            'code': False,
                                                            'color': 'default',
                                                            'italic': False,
                                                            'strikethrough': False,
                                                            'underline': False},
                                            'href': None,
                                            'plain_text': 'Degrowth: Backwards and '
                                                        'Upwards',
                                            'text': {'content': 'Degrowth: Backwards '
                                                                'and Upwards',
                                                    'link': None},
                                            'type': 'text'}],
                                'type': 'title'}},
        'public_url': None,
        'url': 'https://www.notion.so/Degrowth-Backwards-and-Upwards-aab9a1b4a9ff4415a6740a3151ba8a76'
    },
    ...
    ]
    ```json
    """
    srs_blocks: List[Dict] = []
    for page in page_chunk:
        if end_date > datetime.fromisoformat(page["last_edited_time"]):
            return (srs_blocks, True)
        page_id = page["id"]
        some_srs_blocks = search_page_for_blocks_containing_mention(
            page_id, MENTION_TEXT
        )
        srs_blocks.extend(some_srs_blocks)

    return (srs_blocks, False)


def search_page_for_blocks_containing_mention(
    block_id: str, mention_text: str
) -> List[Dict]:
    """Search a Notion page/block for blocks containing a mention text and return any matching blocks

    We recurse on the block if it has any child blocks

    For debugging purposes, here's an example output from the notion.blocks.children.list
    API call:

    ```json
    [
    {
        'archived': False,
        'created_by': {'id': '5be127e8-c6d7-4a7b-a46d-a0eb3bc9d6af',
                      'object': 'user'},
       'created_time': '2024-03-26T10:58:00.000Z',
       'has_children': False,
       'id': '29379cd8-ae47-4282-8353-d1248fbbbc96',
       'last_edited_by': {'id': '5be127e8-c6d7-4a7b-a46d-a0eb3bc9d6af',
                          'object': 'user'},
       'last_edited_time': '2024-03-26T10:58:00.000Z',
       'object': 'block',
       'paragraph': {'color': 'default',
            'rich_text': [{
                'annotations': {
                    'bold': False,
                    'code': False,
                    'color': 'default',
                    'italic': False,
                    'strikethrough': False,
                    'underline': False
                },
                'href': None,
                'plain_text': 'This will be about ',
                'text': {
                    'content': 'This will be about ',
                    'link': None
                },
                'type': 'text'},
                {'annotations': {
                    'bold': False,
                    'code': False,
                    'color': 'default',
                    'italic': False,
                    'strikethrough': False,
                    'underline': False},
                'href': 'https://www.notion.so/0348575723954eac83cf072ec2119d64',
                'mention': {'page': {'id': '03485757-2395-4eac-83cf-072ec2119d64'},
                            'type': 'page'},
                'plain_text': 'degrowth',
                'type': 'mention'},
                {'annotations': {
                    'bold': False,
                    'code': False,
                    'color': 'default',
                    'italic': False,
                    'strikethrough': False,
                    'underline': False},
                'href': None,
                'plain_text': ' and:',
                'text': {'content': ' and:', 'link': None},
                'type': 'text'}]},
       'parent': {'page_id': 'aab9a1b4-a9ff-4415-a674-0a3151ba8a76',
                  'type': 'page_id'},
       'type': 'paragraph'
    },
    {
        'archived': False,
        'created_by': {
            'id': '5be127e8-c6d7-4a7b-a46d-a0eb3bc9d6af',
            'object': 'user'
        },
        'created_time': '2024-03-26T10:58:00.000Z',
        'has_children': False,
        'id': '68217d51-f0e4-45d8-bc36-69dc5cf6f0da',
        'last_edited_by': {
            'id': '5be127e8-c6d7-4a7b-a46d-a0eb3bc9d6af',
            'object': 'user'
        },
        'last_edited_time': '2024-03-26T10:58:00.000Z',
        'numbered_list_item': {
            'color': 'default',
            'rich_text': [{
                'annotations': {
                    'bold': False,
                    'code': False,
                    'color': 'default',
                    'italic': False,
                    'strikethrough': False,
                    'underline': False
                },
                'href': None,
                'plain_text': 'It’s definition',
                'text': {'content': 'It’s definition',
                            'link': None},
                'type': 'text'
            }]
        },
        'object': 'block',
        'parent': {'page_id': 'aab9a1b4-a9ff-4415-a674-0a3151ba8a76',
                    'type': 'page_id'},
        'type': 'numbered_list_item'
    },
    ...
    ]
    ```json
    """

    blocks_with_mentions: List[Dict] = []
    for blocks in iterate_paginated_api(
        notion.blocks.children.list,
        block_id=block_id,
    ):
        some_blocks_with_mentions: List[Dict] = []

        for block in blocks:
            # TODO recursively search through block children
            block_type = block["type"]
            if block_type not in BLOCK_TYPES_TO_PROCESS:
                # these block types contain nothing interesting,
                # continue on
                continue

            # search for the mention within each section of of a block
            # and add the block to our list of mentioned block if it
            # does indeed contain the mention
            for content_section in block[block_type]["rich_text"]:
                if (
                    mention_text in content_section["plain_text"]
                    and not content_section["annotations"]["strikethrough"]
                ):
                    some_blocks_with_mentions.append(block)

            if block["has_children"]:
                # recurse!
                some_blocks_with_mentions.extend(
                    search_page_for_blocks_containing_mention(block["id"], mention_text)
                )

        blocks_with_mentions.extend(some_blocks_with_mentions)
    return blocks_with_mentions


def mark_srs_block_as_processed(block: Dict) -> None:
    """Adds a strikethrough to the mention text in a block to mark it as processed

    This way when we re-run this script, we will ignore this block and
    not double process it
    """
    block_type = block["type"]
    new_rich_text: List[Dict] = []

    for content_section in block[block_type]["rich_text"]:
        content_section["annotations"]["strikethrough"] = True
        new_rich_text.append(content_section)

    block[block_type]["rich_text"] = new_rich_text
    updated_block = notion.blocks.update(block["id"], block)

    return updated_block
