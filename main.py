from lib.intelligence import generate_anki_cloze_card


# This is the entrypoint to your program
def main():
    user_provided_paragraph = "The first-ever comprehensive assessment of net population changes in the U.S. and Canada reveals across-the-board declines that scientists call “staggering.” All told, the North American bird population is down by 3 billion breeding adults, with devastating losses among birds in every biome. 30% of the total American bird population has been lost."
    user_provided_topic = "Environmental Science and Ecology"
    anki_card = generate_anki_cloze_card(user_provided_paragraph, user_provided_topic)
    print(anki_card)


# This makes it so you can run `python main.py` to run this file
if __name__ == "__main__":
    main()
