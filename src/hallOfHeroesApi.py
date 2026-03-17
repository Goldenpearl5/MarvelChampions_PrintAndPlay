# default modules
import json
import os

# pip modules
import wget

# local modules
import config as config

CARD_IMG_BASE_URL = "https://hallofheroeslcg.com/wp-content/uploads"
cardImgUrls = {}


def initApi():
    # load JSON file
    packInfo = None
    with open("cardInfo/packInfo.json") as json_file:
        packInfo = json.load(json_file)

    # load JSON file
    cardDataByPack = None
    with open("cardInfo/medRezCards.json") as json_file:
        cardDataByPack = json.load(json_file)
    
    # populate all card image URLS
    global cardImgUrls
    cardImgUrls = {}
    for packName in cardDataByPack.keys():
        packId = packInfo[packName]["marvelCdbId"]
        for cardData in cardDataByPack[packName]:
            cardId = str(packId)
            cardId += str(cardData["cardId"])
            if "side" in cardData:
                cardId += str(cardData["side"])
            cardImgUrls[cardId] = {
                "imgSrc": f"{CARD_IMG_BASE_URL}/{cardData['src']}",
                "cardName": cardData["cardName"]
            }

def download_card_img_by_card_id(card_id, log_missing_image=True):
    if card_id not in cardImgUrls:
        raise "Error; unknown card ID {card_id}"
    card_name = cardImgUrls[card_id]["cardName"]
    card_img_url = cardImgUrls[card_id]["imgSrc"]
    card_img_path = f"{config.CARD_IMGS_FOLDER_HALL_OF_HEROES}/{card_id}.jpg"

    # Create card_imgs folder, if it doesnt exist
    if(not os.path.exists(config.CARD_IMGS_FOLDER_HALL_OF_HEROES)):
        os.makedirs(config.CARD_IMGS_FOLDER_HALL_OF_HEROES)

    # Download the image, if it doesnt exist
    if(not os.path.exists(card_img_path)):
        print(f"Downloading image for {card_name} ({card_id})")
        try:
            wget.download(card_img_url, out=card_img_path)
        except:
            if(log_missing_image):
                print(f"ERROR: Could not download an image for {card_name} ({card_id})")


initApi()
download_card_img_by_card_id("58001b")