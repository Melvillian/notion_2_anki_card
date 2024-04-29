# notion_2_anki_card

A set of 2 Python script commands, one command for pulling information marked in
Notion as suitable for Anki card generation and using an LLM to generate the
card text, and another command for actually generating the Anki card and storing
it in the Anki deck specified in the `.env` file

## Getting Started

    1. Install [Nix here](https://github.com/DeterminateSystems/nix-installer)
    2. Clone repo with `git clone git@github.com:Melvillian/notion_2_anki_card.git`
    3. Create a [Notion API Secret Key using this guide](https://developers.notion.com/docs/create-a-notion-integration#create-your-integration-in-notion)
    4. Create an OpenAI API Key following [these instruction](https://platform.openai.com/docs/api-reference/authentication)
    5. Create your `.env` file using the `.env.example` as a template
    6. Activate dev environment with `nix develop`
    7. Run the Notion scan command using `python main.py scan_notion` inside of your Nix dev environment. This will generate an `out/cards.pkl` file of all the Anki card text
    8. Run the Anki card acceptance and generation command using `python main.py generate_cards` inside of your Nix dev environment. This will prompt you to review the cards, and any you accept will be added as Anki cards to your Anki Deck
    8. Finally, figure out how to create a cron job (using either [cron](https://phoenixnap.com/kb/set-up-cron-job-linux) or [launchd](https://alvinalexander.com/mac-os-x/mac-osx-startup-crontab-launchd-jobs/) if you're using a Mac) to execute the `main.py scan_notion` and `main.py generate_cards` scripts

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
- [x] split text inference and card creation into 2 steps, so that I can
      manually decide whether or not I want a certain card to be created (I'll
      create a cron job that runs at most once a day whenever I open a new tmux
      session that prompts me to approve or delete new cards created by
      notion_2_anki_card)
- [ ] (Optional): right now the @srs-items are single block, we could extend
      them to be multi-block (though I'm not sure why I would want that right
      now)
- [ ] ensure that anki cart text always contains at least 1 {{c1::}} element. I
      noticed some of the output from cards does not
- [ ] After using the script for a couple weeks, go back and tighten the error
      handling for the LLM output. In particular, I noticed that if you feed it
      nonsense text, it will respond with a card related to the prompt,
      specifically about energy economics. It should instead ignore nonsense
      text and reject making a card, however I'm too lazy to implement and test
      that now.
