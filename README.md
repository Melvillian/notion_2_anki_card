# notion_2_anki_card

A small Python cron script for converting information stored in Notion into Anki
cards

## Getting Started

    1. Install [Nix here](https://github.com/DeterminateSystems/nix-installer)
    2. Clone repo with `git clone git@github.com:Melvillian/notion_2_anki_card.git`
    3. Create a [Notion API Secret Key using this guide](https://developers.notion.com/docs/create-a-notion-integration#create-your-integration-in-notion)
    4. Create your `.env` file using the `.env.example` as a template
    5. Activate dev environment with `nix develop`
    6. Run the app using `python main.py` inside of your Nix dev environment
    7. Finally, figure out how to create a cron job (using either [cron](https://phoenixnap.com/kb/set-up-cron-job-linux) or [launchd](https://alvinalexander.com/mac-os-x/mac-osx-startup-crontab-launchd-jobs/) if you're using a Mac) to execute the `main.py` script

## TODO

- [x] refactor notion_api.py from roam_2_notion to get the following features:
  - [x] get previous 1 week's most edited pages recursively
  - [x] get page content, title, last_edited_time
  - [x] update page to strikethrough any blocks containing @srs-item
- [x] look for @srs-item blocks (that are not strikedthrough) within all page
      content (recursively advance through blocks)
- [x] create anki card data using data from notion and LLM
- [x] add actual anki cards to my local deck
- [ ] make it easy to build a single executable so I can make a cronjob out of
      it
- [ ] (Optional): right now the @srs-items are single block, we could extend
      them to be multi-block (though I'm not sure why I would want that right
      now)
- [ ] After using the script for a couple weeks, go back and tighten the error
      handling for the LLM output. In particular, I noticed that if you feed it
      nonsense text, it will respond with a card related to the prompt,
      specifically about energy economics. It should instead ignore nonsense
      text and reject making a card, however I'm too lazy to implement and test
      that now.
