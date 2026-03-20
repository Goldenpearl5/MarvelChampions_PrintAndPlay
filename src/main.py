# default modules
import argparse

# local modules
import config as config
import marvelCdbApi as marvelCdbApi
import mchPrintAndPlay as mchPrintAndPlay

# Handle command args
parser = argparse.ArgumentParser(description="Marvel Champions Print-And-Play") 
parser.add_argument("-deckId", help="The deck ID from marvelcdb.com") 
parser.add_argument("--disableCardSpacers", action="store_true", help="Disable whitespace between cards?") 
parser.add_argument("--debugLogs", action="store_true", help="Enable debugLogs") 
parser.add_argument("--hideHeroPack", action="store_false", help="Hide hero-specific cards")
parser.add_argument("--offlineMode", action="store_true", help="Insert txt file name instead of deck ID")
parser.add_argument("--initOfflineMode", action="store_true", help="Download ALL card info to support future offline runts") 

args = parser.parse_args() 

debug_logs = args.debugLogs
card_spacers = not args.disableCardSpacers
hide_hero_pack = not args.hideHeroPack
offline_mode = args.offlineMode
init_offline_mode = args.initOfflineMode

if(init_offline_mode):
    print(f"INITIALIZING OFFLINE MODE.")
    print(f"This will download ALL card images, and will take some time.")
    continueInput = input("Continue? (y/n)")
    if (continueInput == "y" or continueInput == "Y"):
        marvelCdbApi.init_card_data(offline_mode, init_offline_mode)
    else:
        "Init cancelled."

# parse deck ID
deck_id = None
if args.deckId:
    deck_id = args.deckId

# allow the user to enter the deck ID
if(not deck_id):
    if offline_mode:
        deck_id = input("Please enter the deck.txt filename (e.g. sampleDeck.txt): ")
    else:
        deck_id = input("Please enter the deck_id (e.g. 60116): ") # example ID, taken from the front page of marvelcdb.com

print("\nCONFIG:")
print(f"The deck ID is: {deck_id}")
print(f"Card spacers: {'enabled' if card_spacers else 'disabled'}.")
print(f"Hero cards: {'hidden' if hide_hero_pack else 'visible'}.")
print(f"Offline Mode: {'true' if offline_mode else 'false'}.")


# init config
config.initConfig(card_spacers=card_spacers)

### Main
# VS code/python debugger was adding weird stuff in print buffer, so flush it.
print('', flush=True) 

# grab name/info for all card IDs
print("\nSTEP 1: Preparing global card details\n")
marvelCdbApi.init_card_data(offline_mode)

# retrieve decklist
print("\nSTEP 2: Getting card ids from deck\n")
deck_obj = None
if(offline_mode):
    deck_txt_path = f"{config.DECKLIST_FOLDER}/{deck_id}"
    deck_obj = marvelCdbApi.get_deck_info_from_decklist_file(deck_txt_path, hide_hero_pack)
else:
    deck_obj = marvelCdbApi.download_deck_info_by_deck_id(deck_id, hide_hero_pack)

card_ids = deck_obj["card_ids"]
deck_name = deck_obj["deck_name"]
card_quantities = deck_obj["card_quantities"]
card_data = deck_obj["card_data"]

# download card images in deck
print("\nSTEP 3: Downloading card images\n")
marvelCdbApi.download_card_imgs_in_list(card_ids) 

# assemble PDF from card images
mchPrintAndPlay.create_deck_pdf_from_card_ids(card_quantities, card_data, deck_name)



