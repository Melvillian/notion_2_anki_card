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
SEARCH_PERIOD_DAYS = 7

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
        page_title = page["properties"]["title"]["title"][0]["text"]["content"]
        page_id = page["id"]
        page_url = page["url"]
        pprint((page_title, page_id, page_url))

        some_srs_blocks = search_page_for_blocks_containing_mention(
            page_id, MENTION_TEXT
        )
        srs_blocks.extend(some_srs_blocks)

    return (srs_blocks, False)


def search_page_for_blocks_containing_mention(
    page_id: str, mention_text: str
) -> List[Dict]:
    """Search a Notion page for blocks containing a mention textand return any matching blocks

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
                     'rich_text': [{'annotations': {'bold': False,
                                                    'code': False,
                                                    'color': 'default',
                                                    'italic': False,
                                                    'strikethrough': False,
                                                    'underline': False},
                                    'href': None,
                                    'plain_text': 'This will be about ',
                                    'text': {'content': 'This will be about ',
                                             'link': None},
                                    'type': 'text'},
                                   {'annotations': {'bold': False,
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
                                   {'annotations': {'bold': False,
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
        'created_by': {'id': '5be127e8-c6d7-4a7b-a46d-a0eb3bc9d6af',
                        'object': 'user'},
        'created_time': '2024-03-26T10:58:00.000Z',
        'has_children': False,
        'id': '68217d51-f0e4-45d8-bc36-69dc5cf6f0da',
        'last_edited_by': {'id': '5be127e8-c6d7-4a7b-a46d-a0eb3bc9d6af',
                            'object': 'user'},
        'last_edited_time': '2024-03-26T10:58:00.000Z',
        'numbered_list_item': {'color': 'default',
                                'rich_text': [{'annotations': {'bold': False,
                                                            'code': False,
                                                            'color': 'default',
                                                            'italic': False,
                                                            'strikethrough': False,
                                                            'underline': False},
                                            'href': None,
                                            'plain_text': 'It’s definition',
                                            'text': {'content': 'It’s definition',
                                                        'link': None},
                                            'type': 'text'}]},
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
        block_id=page_id,
    ):
        some_blocks_with_mentions: List[Dict] = []

        for block in blocks:
            # TODO recursively search through block children
            block_type = block["type"]
            if block_type not in BLOCK_TYPES_TO_PROCESS:
                # these block types contain nothing interesting,
                # continue on
                continue

            print("BLOCK DATA")
            pprint(block)

            # search for the mention within each section of of a block
            # and add the block to our list of mentioned block if it
            # does indeed contain the mention
            for content_section in block[block_type]["rich_text"]:
                if mention_text in content_section["plain_text"]:
                    some_blocks_with_mentions.append(block)

        blocks_with_mentions.extend(some_blocks_with_mentions)
    return blocks_with_mentions


def normalize_chars(text: str) -> str:
    """
    Given a string, replace all strange characters with their ascii equivalents

    This is necessary because of symbols like an apostrophe that can be
    represented in multiple ways (e.g. "’" and "'") and we want to use
    the representation that will allow us to look up the correct pages
    in Notion

    Note: we may need to add more characters to this list in the future,
    but for now it solves the problem we're facing
    """

    for i in range(len(text)):
        # get the unicode code point for the current character
        code_point = ord(text[i])
        if code_point == 8217:  # unicode for right apostrophe
            # replace it with the ascii equivalent
            text = text[:i] + "'" + text[i + 1 :]
    return text


####################################### OLD #######################################

NOTION_KEY = os.environ.get("NOTION_KEY")
NOTION_VERSION = "2022-06-28"
NOTION_API_PREFIX = "https://api.notion.com/v1"
CURSOR_METADATA_FILENAME = "cursor_metadata.json"
SHARED_SEARCH_PARAMS: dict[str, Any] = {
    "filter": {"value": "page", "property": "object"},
    "sort": {"direction": "ascending", "timestamp": "last_edited_time"},
}

# sometimes we fail for some reason on Notion's end,
# and it is a transitory failure. So we retry a few times
# but after a certain number of failed tries we abort
SLEEP_TIME_FAILURE_SECS = 10
MAX_FAILURE_TRIES = 100


HEADERS = {
    "Authorization": f"Bearer {NOTION_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


class NoPageFoundException(Exception):
    pass


def search_for_page(page_name: str) -> tuple[str, str]:
    """
    Search for page id and url that matches the given page name

    Args:
        page_name (str): Page name to search for

    Returns:
        tuple[str, str]: Tuple of the page id and url, or raise Exception if no match found
    """

    # some characters like apostrophe "'" have multiple representations
    # in unicode, so normalize the page_name so we can properly compare
    # it in the loop below
    page_name = normalize_chars(page_name)
    page_name = page_name.lower()

    search_params = copy.deepcopy(SHARED_SEARCH_PARAMS)
    search_params["query"] = page_name

    # a single search query might result in multiple pages of results, so
    # loop over the paginated Notion results, searching for a case-insensitive
    # match so we can extract the id and url
    has_more = True
    next_cursor = None

    while has_more:
        if next_cursor:
            search_params["start_cursor"] = next_cursor

        search_response = post(
            f"{NOTION_API_PREFIX}/search", json=search_params, headers=HEADERS
        )
        response = search_response.json()

        for result in response["results"]:
            # we use .lower() because Roam Research's page names were
            # case insensitive, so a raw literal could be [[ai]] but
            # the page name could be AI. So we need to make them both
            # lowercase so that then we can do an exact == comparison
            title = result["properties"]["title"]["title"][0]["plain_text"].lower()
            title = normalize_chars(title)
            if title == page_name:
                return (result["id"], result["url"])

        has_more = response["has_more"]
        next_cursor = response["next_cursor"]

    raise NoPageFoundException(f"No page found with name {page_name}")


def search_for_pages() -> dict[str, Any]:
    """
    Searches for all pages in the user's Notion workspace

    Based on the Notion API key you're using and the pages that have been
    shared with the key's integration, return all of the pages' properties
    (but not their content) in the user's workspace. This contains page ID's
    which can be used to access each page's content using the block API

    Args:

    Returns:
        dict: a dictionary of search results and cursor data
        {
            "object": "list",
            "results": [
                {
                    "object": "page",
                    "id": "afb8dbd2-1d10-43da-bc15-87d6f6c682aa",
                    "created_time": "2023-06-22T12:40:00.000Z",
                    "last_edited_time": "2023-12-20T20:39:00.000Z",
                    "created_by": {
                        "object": "user",
                        "id": "5be127e8-c6d7-4a7b-a46d-a0eb3bc9d6af"
                    },
                    "last_edited_by": {
                        "object": "user",
                        "id": "5be127e8-c6d7-4a7b-a46d-a0eb3bc9d6af"
                    },
                    "cover": null,
                    "icon": null,
                    "parent": {
                        "type": "page_id",
                        "page_id": "7b1b3b0c-14cb-45a6-a4b6-d2b48faecccb"
                    },
                    "archived": false,
                    "properties": {
                        "title": {
                            "id": "title",
                            "type": "title",
                            "title": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "cyberwizard",
                                        "link": null
                                    },
                                    "annotations": {
                                        "bold": false,
                                        "italic": false,
                                        "strikethrough": false,
                                        "underline": false,
                                        "code": false,
                                        "color": "default"
                                    },
                                    "plain_text": "cyberwizard",
                                    "href": null
                                }
                            ]
                        }
                    },
                    "url": "https://www.notion.so/cyberwizard-afb8dbd21d1043dabc1587d6f6c682aa",
                    "public_url": null
                },
                ...
            ],
            "next_cursor": "3ad0febc-4d86-4fda-882d-ee902cf66fb8",
            "has_more": true,
            "request_id": "a20cf866-9d69-45cf-a62a-f88d9159d7ad"
        }
    """

    search_params = copy.deepcopy(SHARED_SEARCH_PARAMS)

    # we must be searching through all the pages, so this is the cursor
    # that will be used to fetch the next page of results
    next_cursor = None

    # we store the cursor data in a file in case the script fails partway
    # and we need to start from where we left off
    if os.path.isfile(CURSOR_METADATA_FILENAME):
        with open(CURSOR_METADATA_FILENAME) as f:
            cursor_metadata = json.load(f)
            next_cursor = cursor_metadata["next_cursor"]
    if next_cursor:
        search_params["start_cursor"] = next_cursor

    search_response = post(
        f"{NOTION_API_PREFIX}/search", json=search_params, headers=HEADERS
    )

    return search_response.json()


def generate_mention_section(mention_page_name: str) -> dict[str, Any]:
    """
    Create a mention section for the block.

    This is the real purpose of the script, to create these mention sections
    for sections of text that currently contain mentions to other pages, but
    using the literal [[...]] syntax from Roam Research
    """

    print(f"Creating mention section for {mention_page_name}")

    (page_id, href) = search_for_page(mention_page_name)

    new_section = {
        "annotations": {
            "bold": False,
            "code": False,
            "color": "default",
            "italic": False,
            "strikethrough": False,
            "underline": False,
        },
        "href": href,
        "mention": {"page": {"id": page_id}, "type": "page"},
        "plain_text": mention_page_name,
        "type": "mention",
    }

    return new_section


def generate_text_section(section_text: str) -> dict[str, Any]:
    """
    Create a text section for the block.

    This is pretty boring, because it just contains simple plaintext,
    no mentions
    """
    new_section = {
        "annotations": {
            "bold": False,
            "code": False,
            "color": "default",
            "italic": False,
            "strikethrough": False,
            "underline": False,
        },
        "href": None,
        "plain_text": section_text,
        "text": {"content": section_text, "link": None},
        "type": "text",
    }

    return new_section


def check_for_and_update_block(block_id: str, block: dict[str, Any]) -> None:
    """
    Check if a block contains any [[...]] literals, and if so,
    update the block in Notion so that all literal [[...]] are replaced with
    mentions.

    Replaces block data that looks like this:

    ```json
    {
        "annotations": {
            "bold": false,
            "code": false,
            "color": "default",
            "italic": false,
            "strikethrough": false,
            "underline": false
        },
        "href": null,
        "plain_text": "[[Capital Manifesto]] is a good book to read on this subject, as well as ",
        "text": {
            "content": "[[Capital Manifesto]] is a good book to read on this subject, as well as ",
            "link": null
        },
        "type": "text"
    },
    ```

    with this, where the [[...]] has been removed and replaced with a mention
    section:

    ```json
    {
        "annotations": {
            "bold": false,
            "code": false,
            "color": "default",
            "italic": false,
            "strikethrough": false,
            "underline": false
        },
        "href": "https://www.notion.so/8d16c7abf8a74c7a8fee597edc05cafa",
        "mention": {
            "page": {
                "id": "8d16c7ab-f8a7-4c7a-8fee-597edc05cafa"
            },
            "type": "page"
        },
        "plain_text": "Capitalist Manifesto",
        "type": "mention"
    },
    {
        "annotations": {
            "bold": false,
            "code": false,
            "color": "default",
            "italic": false,
            "strikethrough": false,
            "underline": false
        },
        "href": null,
        "plain_text": " is a good book to read on this subject, as well as ",
        "text": {
            "content": " is a good book to read on this subject, as well as ",
            "link": null
        },
        "type": "text"
    }
    ```
    """

    old_content = block["content"]
    if not old_content["rich_text"]:
        # this is a boring empty block, so we do not update
        # anything and simply return
        return

    # update this to True if this block contains any
    # literals [[...]] we need to turn into mentions
    needs_update = False

    # start building the new block content that we'll use to overwrite
    # (i.e. overwrite) the old block contents
    new_content = []
    for content_section in old_content["rich_text"]:
        virtual_text = create_virtual_text(content_section["plain_text"])

        if not any(tup[1] for tup in virtual_text):
            # this section of the block doesn't contain any literal [[...]]
            # text which should be turned into mentions, so we should leave
            # it as is by simply appending the existing old section to the
            # new block's content
            new_content.append(content_section)
            continue

        needs_update = True
        # this section of block contains literal [[...]] text
        # which should be turned into mentions so we'll need to
        # build a new section for each mention and for each plaintext,
        # and append it to the new block
        for section in virtual_text:
            section_text = section[0]
            is_mention = section[1]

            new_section = (
                generate_mention_section(section_text)
                if is_mention
                and "/"
                not in section_text  # our script can't handle "/" page names, so skip them
                else generate_text_section(section_text)
            )
            new_content.append(new_section)

    if not needs_update:
        # No literal [[...]] sections found in this block,
        # so no need to update it
        return

    # this is the object we'll write to the Notion API to update the block
    block_type = block["type"]
    new_content_block = {
        block_type: {
            "color": old_content["color"],
            "rich_text": new_content,
        }
    }

    url = f"{NOTION_API_PREFIX}/blocks/{block_id}"
    patch(url, headers=HEADERS, json=new_content_block)


def fetch_block_children(block_id: str) -> dict[str, Any]:
    """
    Given a Block ID (which may be a Page ID), return a dict keyed by
    all of the given block/page's block IDs, and the child's data.
    This includes children of children, recursively (so we get all of the
    blocks in the page, not just the top level blocks).

    The important value will be the `content` field, which contains an
    array of objects of type `text` and `mention` (there could also be equation
    in the original block, but we ignore those)

    Returns:
        dict: a dict keyed by block ID, and the value is a dict containing the
        block's type. For example:
        ```json
        {
            "13b5fa46-4308-4e19-a22b-67d440a017b6": {
                "has_children": false,
                "content": {
                    "color": "default",
                    "rich_text": []
                },
                "type": "paragraph"
            },
            "407c0a7b-5759-461c-a082-59c52f670bf5": {
                "has_children": false,
                "content": {
                    "color": "default",
                    "rich_text": [
                        {
                            "annotations": {
                                "bold": false,
                                "code": false,
                                "color": "default",
                                "italic": false,
                                "strikethrough": false,
                                "underline": false
                            },
                            "href": "https://www.notion.so/8d16c7abf8a74c7a8fee597edc05cafa",
                            "mention": {
                                "page": {
                                    "id": "8d16c7ab-f8a7-4c7a-8fee-597edc05cafa"
                                },
                                "type": "page"
                            },
                            "plain_text": "Capitalist Manifesto",
                            "type": "mention"
                        },
                        {
                            "annotations": {
                                "bold": false,
                                "code": false,
                                "color": "default",
                                "italic": false,
                                "strikethrough": false,
                                "underline": false
                            },
                            "href": null,
                            "plain_text": " is a good book to read on this subject, as well as ",
                            "text": {
                                "content": " is a good book to read on this subject, as well as ",
                                "link": null
                            },
                            "type": "text"
                        },
                        {
                            "annotations": {
                                "bold": false,
                                "code": false,
                                "color": "default",
                                "italic": false,
                                "strikethrough": false,
                                "underline": false
                            },
                            "href": "https://www.notion.so/3cdb2c5ad41e4a8d8321d36cf14947a9",
                            "mention": {
                                "page": {
                                    "id": "3cdb2c5a-d41e-4a8d-8321-d36cf14947a9"
                                },
                                "type": "page"
                            },
                            "plain_text": "Karl Marx",
                            "type": "mention"
                        },
                        {
                            "annotations": {
                                "bold": false,
                                "code": false,
                                "color": "default",
                                "italic": false,
                                "strikethrough": false,
                                "underline": false
                            },
                            "href": null,
                            "plain_text": "  since they are opposed to each other, especially now. One more is ",
                            "text": {
                                "content": "  since they are opposed to each other, especially now. One more is ",
                                "link": null
                            },
                            "type": "text"
                        },
                        {
                            "annotations": {
                                "bold": false,
                                "code": false,
                                "color": "default",
                                "italic": false,
                                "strikethrough": false,
                                "underline": false
                            },
                            "href": "https://www.notion.so/18c9042fe0b743c8943769c8b668720c",
                            "mention": {
                                "page": {
                                    "id": "18c9042f-e0b7-43c8-9437-69c8b668720c"
                                },
                                "type": "page"
                            },
                            "plain_text": "venture capital",
                            "type": "mention"
                        },
                        {
                            "annotations": {
                                "bold": false,
                                "code": false,
                                "color": "default",
                                "italic": false,
                                "strikethrough": false,
                                "underline": false
                            },
                            "href": null,
                            "plain_text": " ",
                            "text": {
                                "content": " ",
                                "link": null
                            },
                            "type": "text"
                        }
                    ]
                },
                "type": "paragraph"
            },
            "7ea896f8-6b29-4928-9883-e82625417bf4": {
                "has_children": false,
                "content": {
                    "color": "default",
                    "rich_text": []
                },
                "type": "paragraph"
            },
            "832edff3-8520-49ee-925f-17f5c5c7175e": {
                "has_children": false,
                "content": {
                    "color": "default",
                    "rich_text": [
                        {
                            "annotations": {
                                "bold": false,
                                "code": false,
                                "color": "default",
                                "italic": false,
                                "strikethrough": false,
                                "underline": false
                            },
                            "href": null,
                            "plain_text": "another one ",
                            "text": {
                                "content": "another one ",
                                "link": null
                            },
                            "type": "text"
                        }
                    ]
                },
                "type": "paragraph"
            }
        }
        ```
    """

    has_more = True
    next_cursor = None
    block_children = {}
    base_url = f"{NOTION_API_PREFIX}/blocks/{block_id}/children"

    while has_more:
        url = base_url
        if next_cursor:
            url += f"?start_cursor={next_cursor}"
        response = get(url, headers=HEADERS)
        response = response.json()

        for block in response["results"]:
            if block["type"] in BLOCK_TYPES_TO_PROCESS:
                block_type = block["type"]

                block_children[block["id"]] = {
                    "type": block_type,
                    "content": block[block_type],
                }

                # recurse if there are any children, aggregating all the
                # block and child block content into one dict
                if block["has_children"]:
                    sub_block_children = fetch_block_children(block["id"])
                    for sub_block_id, sub_child in sub_block_children.items():
                        block_children[sub_block_id] = sub_child

        has_more = response["has_more"]
        next_cursor = response["next_cursor"]

    return block_children


def extract_page_name_and_id(page: dict[str, Any]) -> tuple[str, str]:
    """
    Helper function to extract the page name and ID from a page object.
    """
    title_data = page["properties"]["title"]["title"]
    assert len(title_data) == 1, (
        f"only one title allowed per page, but found {len(title_data)}"
        f"for page:\n{title_data[0]['plain_text']}"
    )
    page_name = title_data[0]["plain_text"]
    assert page_name == title_data[0]["text"]["content"], (
        f"title data is not consistent: "
        f"{page_name}, {title_data[0]['text']['content']}"
    )
    page_id = page["id"]
    return page_name, page_id


def process_single_page(page_id: str) -> None:
    """
    A convenience function to process a single page.

    Mostly used for debugging when a single page causes a
    failure and you want to go back and manually process
    that single page.
    """
    block_children = fetch_block_children(page_id)
    for block_id, block in block_children.items():
        check_for_and_update_block(block_id, block)
