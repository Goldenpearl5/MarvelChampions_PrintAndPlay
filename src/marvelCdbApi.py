# default modules
import json
import os
import re

# pip modules
import requests
import wget

# local modules
import config as config

all_card_data = {}
all_card_ids_by_pack_code = {}

all_pack_data = {}
all_pack_codes_by_name = {} # e.g. all_pack_codes_by_name["Core Set"] = "core"

def init_card_data(use_offline_mode=False, init_offline_mode=False):
    global all_card_data

    if(init_offline_mode):
        download_data_for_offline_mode(download_all_imgs=True)

    if(use_offline_mode):
        # First time setup
        if not os.path.isfile(config.ALL_CARD_INFO_JSON):
            download_data_for_offline_mode(download_all_imgs=False)

        # Load JSON file
        with open(config.ALL_CARD_INFO_JSON) as json_file:
            global all_card_data
            all_card_data = json.load(json_file)
            print(f"JSON file loaded ({config.ALL_CARD_INFO_JSON})")
    else:
        all_card_data = download_all_card_info()

def download_all_card_info():
    # download data dump
    apiUrl = "https://marvelcdb.com/api/public/cards/"
    response = requests.get(apiUrl)
    apiData = response.json()

    # process data dump
    allCards = {}
    for apiCardObj in apiData:
        cardObj = parse_card_obj_from_api(apiCardObj)
        allCards[cardObj["cardId"]] = cardObj
    
    return allCards

# Needed for card lookup in offline mode
def init_pack_data():
    global all_pack_data
    global all_pack_data_by_name
    
    # sort cards by pack
    for cardId, cardObj in all_card_data.items():
        pack_code = cardObj["packCode"]
        if pack_code not in all_card_ids_by_pack_code.keys():
            all_card_ids_by_pack_code[pack_code] = []
        all_card_ids_by_pack_code[pack_code].append(cardId)

    # Load pack details
    with open(config.ALL_PACK_INFO_JSON) as json_file:
        all_pack_data = json.load(json_file)
    
    # Map pack name to pack code
    for packCode, packObj in all_pack_data.items():
        all_pack_codes_by_name[packObj["name"]] = packCode

def download_deck_info_by_deck_id(deck_id, hide_hero_pack=False):
    # Make an API call
    data = None
    try:
        # try public listing URL
        apiUrl = f"https://marvelcdb.com/api/public/decklist/{deck_id}"
        response = requests.get(apiUrl)
        data = response.json()
    except:
        try:
            # try private listing URL
            apiUrl = f"https://marvelcdb.com/api/public/deck/{deck_id}"
            response = requests.get(apiUrl)
            data = response.json()
        except:
            print(f"Could not locate deck id {deck_id}")

    deck_name = data.get('name')
    print(f"Deck Name: {deck_name}")

    # Parse the JSON Response
    card_quantities = data.get('slots', {}) # dictionary of card ID to card quantity. e.g. cardQuantities["12015"] = 3
    card_ids = card_quantities.keys()
    print("Decklist retrieved.")

    # Retrieve detailed info on each card
    card_data = {}
    for card_id in card_ids:
        if(card_id in all_card_data):
            card_data[card_id] = all_card_data[card_id]
        else:
            # note; this should never be hit if init_card_data() was run 
            card_data[card_id] = download_card_info_by_card_id(card_id)
    print("Card info retrieved.")

    # Remove hero cards, if needed
    if (hide_hero_pack):
        for card_id in card_quantities.keys():
            if card_data[card_id]["factionCode"] == "hero":
                card_quantities[card_id] = 0
        print("Hero cards removed.")

    # Return deck info
    return {
        "card_ids": card_ids,
        "card_quantities": card_quantities,
        "card_data": card_data,
        "deck_name": deck_name
    }

def get_deck_info_from_decklist_file(filePath, hide_hero_pack=False):
    # load relevant data
    init_pack_data()

    # declare deck variables
    deck_title = ""
    card_ids = []
    card_quantities = {}
    card_data = {}
   
    # read decklist text file
    fileContents = []
    with open(filePath) as file:
        fileContents = file.read().split("\n")
        for line in file:
            fileContents.append(line)

    # iterate file contents line by line
    CARD_REGEX = r'(\d)x (.+)\s\((.+)\)'
    totalCards = 0
    for idx, deckLine in enumerate(fileContents):
        if(idx == 0):
            deck_title = deckLine
        else:
            matchObj = re.fullmatch(CARD_REGEX, deckLine)
            if matchObj != None:
                quantity = int(matchObj[1])
                card_name = matchObj[2]
                pack_name = matchObj[3]

                # locate pack ID
                if pack_name in all_pack_codes_by_name:
                    pack_code = all_pack_codes_by_name[pack_name]
                    card_ids_in_pack = all_card_ids_by_pack_code[pack_code]

                    # locate card ID 
                    card_id = None
                    for test_id in card_ids_in_pack:
                        card_obj = all_card_data[test_id]
                        if card_obj["cardName"] == card_name or card_obj["cardName"].startswith(card_name):
                            card_id = card_obj["cardId"]
                            break

                    if card_id == None:
                        print (f"Unknown card: {card_name}")
                    else:
                        card_ids.append(card_id)
                        card_data[card_id] = all_card_data[card_id]
                        card_quantities[card_id] = quantity
                        totalCards+=quantity

                else:
                    print(f"Unknown pack name {pack_name}")

    # Throw error if decklist was empty
    if totalCards == 0:
        raise "No cards were able to be parsed"
    
    # Log decklist data
    print(f"Decklist parsed. Total Cards: {totalCards}")

    # Remove hero cards, if needed
    if (hide_hero_pack):
        for card_id in card_quantities.keys():
            if card_data[card_id]["factionCode"] == "hero":
                card_quantities[card_id] = 0
        print("Hero cards removed.")

    # Return deck info
    return {
        "card_ids": card_ids,
        "card_quantities": card_quantities,
        "card_data": card_data,
        "deck_name": deck_title
    }

def download_card_info_by_card_id(card_id):
    print(f"Getting card info for {card_id}")
    apiUrl = f"https://marvelcdb.com/api/public/card/{card_id}"
    response = requests.get(apiUrl)
    apiData = response.json()
    return parse_card_obj_from_api(apiData)

def parse_card_obj_from_api(apiData):
    packCode = apiData.get("pack_code")
    position = apiData.get("position")
    quantity = apiData.get("quantity")
    factionCode = apiData.get("faction_code") 
    cardId = apiData.get("code")

    # get card name
    baseName = apiData.get("name")
    subName = apiData.get("subname")
    cardName = baseName
    if subName:
        cardName += f" / {subName}"

    # get reprint status
    isReprint = False
    if "duplicate_of_code" in apiData and len(apiData["duplicate_of_code"]) > 0:
        isReprint = True

    return {
            "cardId": cardId,
            "packCode": packCode,
            "position": position,
            "quantity": quantity,
            "isReprint": isReprint,
            "factionCode": factionCode,
            "cardName": cardName,
    }

def download_card_img_by_card_id(card_id, card_name="Unknown Card", log_missing_image=True):
    card_img_path = f"{config.CARD_IMGS_FOLDER}/{card_id}.png"

    # Create card_imgs folder, if it doesnt exist
    if(not os.path.exists(config.CARD_IMGS_FOLDER)):
        os.makedirs(config.CARD_IMGS_FOLDER)

    # Download the image, if it doesnt exist
    if(not os.path.exists(card_img_path)):
        print(f"Downloading image for {card_name} ({card_id})")

        try:
            card_img_url = (f"https://marvelcdb.com/bundles/cards/{card_id}.png")
            wget.download(card_img_url, out=card_img_path)
        except:
            try:
                card_img_url = (f"https://marvelcdb.com/bundles/cards/{card_id}.jpg")
                wget.download(card_img_url, out=card_img_path)
            except:
                if(log_missing_image):
                    print(f"ERROR: Could not download an image for {card_name} ({card_id})")

    # TODO
    # find a secondary data source

def download_card_imgs_in_list(card_ids):
    for card_id in card_ids:
        download_card_img_by_card_id(card_id, all_card_data[card_id]["cardName"])

def download_all_card_images(all_card_info):
    for cardId, cardObj in all_card_info.items():
        logMissingImage = ("isReprint" in cardObj)
        download_card_img_by_card_id(cardId, cardObj["cardName"], logMissingImage)

def write_all_card_info_to_json(all_card_info):
    # Create card_imgs folder, if it doesnt exist
    if(not os.path.exists(config.CARD_INFO_FOLDER)):
        os.makedirs(config.CARD_INFO_FOLDER)

    with open(config.ALL_CARD_INFO_JSON, "w") as json_file:
        json.dump(all_card_info, json_file, indent=4)

def download_data_for_offline_mode(download_all_imgs=False):
    print("Downloading global card data (this allows offline runs in the future)")
    allCardInfo = download_all_card_info()
    write_all_card_info_to_json(allCardInfo)
    if download_all_imgs:
        print("Downloading ALL card images from MarvelCDB. (This will take a while.)")
        download_all_card_images(allCardInfo)
