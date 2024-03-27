# notion_2_anki_card

A small Python cron script for converting information stored in Notion into Anki
cards

## TODO

- [ ] refactor notion_api.py from roam_2_notion to get the following features:
  - [ ] get previous 2 weeks most edited pages recursively
  - [ ] get page content, title, last_edited_time
  - [ ] update page to strikethrough any blocks containing @srs-item
- [ ] look for @srs-item blocks (that are not strikedthrough) within all page
      content (recursively advance through blocks)
- [ ]
