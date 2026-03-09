# default modules
import os
import math
import sys
import argparse 
#import time

# pip modules
import requests
import wget
from PIL import Image, ImageDraw, ImageFont
import pypdf
import pdfkit

CARD_IMGS_FOLDER = "card_imgs"
DECK_IMGS_FOLDER = "deck_imgs"

# Handle command args
parser = argparse.ArgumentParser(description="Marvel Champions Print-And-Play") 
parser.add_argument("-deckId", help="The deck ID from marvelcdb.com") 
parser.add_argument("--disableCardSpacers", action="store_true", help="Disable whitespace between cards?") 
parser.add_argument("--debugLogs", action="store_true", help="Enable debugLogs") 
parser.add_argument("--hideHeroPack", action="store_false", help="Hide hero-specific cards") 

args = parser.parse_args() 

DEBUG_LOGS = args.debugLogs
CARD_SPACERS = not args.disableCardSpacers
DECK_ID = '60116' # default ID, taken from the front page of marvelcdb.com
HIDE_HERO_PACK = not args.hideHeroPack

if args.deckId:
    DECK_ID = args.deckId
else:
    print("No deck ID provided. A default value will be used.")

print(f"The deck ID is: {DECK_ID}")
print(f"Card spacers are {'enabled' if CARD_SPACERS else 'disabled'}.")
print(f"Hero cards are {'hidden' if HIDE_HERO_PACK else 'visible'}.")

# Calculate page dimensions
CARD_WIDTH_INCHES = 2.5
CARD_HEIGHT_INCHES = 3.5

PAGE_WIDTH_INCHES = 8.5
PAGE_HEIGHT_INCHES = 11

PAGE_X_MARGIN_INCHES = 0.4
PAGE_Y_MARGIN_INCHES = 0.1

CARD_X_SPACER_INCHES = 0.1 if CARD_SPACERS else 0
CARD_Y_SPACER_INCHES = 0.1 if CARD_SPACERS else 0

PDF_PRINTABLE_DPI = 300
PDF_DIGITAL_DPI = 72
PDF_DOWNSCALE_PECENTAGE = (PDF_DIGITAL_DPI/PDF_PRINTABLE_DPI)

CARD_WIDTH_PX = int(CARD_WIDTH_INCHES * PDF_PRINTABLE_DPI)
CARD_HEIGHT_PX = int(CARD_HEIGHT_INCHES * PDF_PRINTABLE_DPI)

PAGE_WIDTH_PX = int(PAGE_WIDTH_INCHES * PDF_PRINTABLE_DPI)
PAGE_HEIGHT_PX = int(PAGE_HEIGHT_INCHES * PDF_PRINTABLE_DPI)

PAGE_X_MARGIN_PX = int(PAGE_X_MARGIN_INCHES * PDF_PRINTABLE_DPI)
PAGE_Y_MARGIN_PX = int(PAGE_Y_MARGIN_INCHES * PDF_PRINTABLE_DPI)

CARD_X_SPACER_PX = int(CARD_X_SPACER_INCHES * PDF_PRINTABLE_DPI)
CARD_Y_SPACER_PX = int(CARD_Y_SPACER_INCHES * PDF_PRINTABLE_DPI)

PRINTABLE_X_SPACE_INCHES = (PAGE_WIDTH_INCHES - (2 * PAGE_X_MARGIN_INCHES))
PRINTABLE_Y_SPACE_INCHES = (PAGE_HEIGHT_INCHES - (2 * PAGE_Y_MARGIN_INCHES))

# Calculate cards per page; multi-step process
CARD_ROWS_PER_PAGE = 0
CARD_COLS_PER_PAGE = 0

CAN_CARDS_FIT_ON_PAGE = False 
if PRINTABLE_Y_SPACE_INCHES >= CARD_HEIGHT_INCHES and PRINTABLE_X_SPACE_INCHES >= CARD_WIDTH_INCHES:
    CAN_CARDS_FIT_ON_PAGE = True

if CAN_CARDS_FIT_ON_PAGE:
    # subtract one spacer instance bc last card has no spacer
    CARD_ROWS_PER_PAGE = 1 + int((PRINTABLE_Y_SPACE_INCHES-CARD_HEIGHT_INCHES) / (CARD_HEIGHT_INCHES + CARD_Y_SPACER_INCHES))
    CARD_COLS_PER_PAGE = 1 + int((PRINTABLE_X_SPACE_INCHES-CARD_WIDTH_INCHES) / (CARD_WIDTH_INCHES + CARD_X_SPACER_INCHES))
CARDS_PER_PAGE = CARD_ROWS_PER_PAGE * CARD_COLS_PER_PAGE


# Log page dimensions
if DEBUG_LOGS:
    print(f"Cards per page: {CARD_COLS_PER_PAGE}x{CARD_ROWS_PER_PAGE}")

    LEFTOVER_X_SPACE = PRINTABLE_X_SPACE_INCHES - (CARD_COLS_PER_PAGE*CARD_WIDTH_INCHES) - ((CARD_COLS_PER_PAGE-1)*CARD_X_SPACER_INCHES)
    LEFTOVER_Y_SPACE = PRINTABLE_Y_SPACE_INCHES - (CARD_ROWS_PER_PAGE*CARD_HEIGHT_INCHES) - ((CARD_ROWS_PER_PAGE-1)*CARD_Y_SPACER_INCHES)
    print(f"leftover space x: {round(LEFTOVER_X_SPACE, 3)}")
    print(f"leftover space y: {round(LEFTOVER_Y_SPACE, 3)}")

def get_card_ids_by_deck_id(deck_id):
    print("\nSTEP 1: Getting card ids from deck\n")
    if(not deck_id):
        deck_id = input("Please enter the deck_id: ")
    # Make an API call
    data = None
    try:
        # try public listing URL
        apiUrl = f"https://marvelcdb.com/api/public/decklist/{deck_id}"
        response = requests.get(apiUrl)
        data = response.json()
    except:
        # try private listing URL
        apiUrl = f"https://marvelcdb.com/api/public/deck/{deck_id}"
        response = requests.get(apiUrl)
        data = response.json()

    deck_name = data.get('name')

    # Parse the JSON Response
    card_slots = data.get('slots', {})
    card_ids = []
    for card_id, needed_quantity in card_slots.items():
        card_quantity = 0
        while card_quantity < needed_quantity:
            card_ids.append(card_id)
            card_quantity += 1
    return {
        "card_ids": card_ids,
        "deck_name": deck_name,
        "card_slots": card_slots
    }

def get_card_name_by_card_id(card_id):
    card_name = "Unknown Card"
    try:
        apiUrl = f"https://marvelcdb.com/api/public/card/{card_id}"
        response = requests.get(apiUrl)
        data = response.json()
        card_name = data.get('name')
    except:
        pass
    return card_name

def hide_hero_pack(card_ids):
    print("Hiding Hero cards")
    card_ids_without_hero = []
    for card_id in card_ids:
        apiUrl = f"https://marvelcdb.com/api/public/card/{card_id}"
        response = requests.get(apiUrl)
        data = response.json()
        faction_code = data.get('faction_code')
        card_name = data.get('name')
        if faction_code != "hero":
            card_ids_without_hero.append(card_id)
        else:
            print(f"Removed {card_name}.")
    return card_ids_without_hero

def download_card_img_by_card_id(card_id):
    card_img_path = f"{CARD_IMGS_FOLDER}/{card_id}.png"

    # Create card_imgs folder, if it doesnt exist
    if(not os.path.exists(CARD_IMGS_FOLDER)):
        os.mkdir(CARD_IMGS_FOLDER)

    # Download the image, if it doesnt exist
    if(not os.path.exists(card_img_path)):

        # Retrieve card name
        card_name = get_card_name_by_card_id(card_id)
        print(f"Downloading image for {card_name} ({card_id})")

        try:
            card_img_url = (f"https://marvelcdb.com/bundles/cards/{card_id}.png")
            wget.download(card_img_url, out=card_img_path)
        except:
            try:
                card_img_url = (f"https://marvelcdb.com/bundles/cards/{card_id}.jpg")
                wget.download(card_img_url, out=card_img_path)
            except:
                print(f"ERROR: Could not download an image for {card_name} ({card_id})")

    # TODO
    # find a secondary data source

def create_summary_card_img(card_slots, deck_name=""):
    response = requests.get(f"https://marvelcdb.com/api/public/cards/")
    all_cards = response.json()
    all_cards_mapped = {}
    for card_obj in all_cards:
        all_cards_mapped[card_obj["code"]] = card_obj
    
    # TODO sort by card type
    deck_summary = f"{deck_name}\n"
    deck_summary_html_str = f"<span class='deckTitle'>{deck_name}</span><br>"
    deck_summary_html_str +=f"<span class='deckSubtitle'>{deck_name}</span><br>"
    deck_summary_html_str +="<span class='aspectLabel'>test</span><br>"
    deck_summary_html_str +="<span class='heroLabel'>test</span><br>"
    for card_id, card_quantity in card_slots.items():
        # all_cards_mapped[card_id]["type_name"]
        deck_summary += (all_cards_mapped[card_id]["name"] + " x" + str(card_quantity) +"\n")



    # Configure pdfkit
    config = pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe')
    options = {
        'page-size': 'Letter',
        'margin-top': '0.35in',
        'margin-right': '0.35in',
        'margin-bottom': '0.35in',
        'margin-left': '0.35in',
        'encoding': 'UTF-8',
    }
    css = 'deck_summary_card.css'
    pdfkit.from_string(deck_summary_html_str, 'out5.pdf', configuration=config, options=options, css=css)
    print(deck_summary)

def create_deck_pdf_from_card_ids(card_ids, deck_name=""):
    print("\nSTEP 3: Creating a PDF\n")
    # Create deck_imgs folder, if it doesnt exist
    if(not os.path.exists(DECK_IMGS_FOLDER)):
        os.mkdir(DECK_IMGS_FOLDER)

    # Create a list of card images.
    card_imgs=[]
    for card_id in card_ids:
        card_img = None
        try:
            # load card image
            card_img = Image.open(f"{CARD_IMGS_FOLDER}/{card_id}.png").convert("RGB");

            # Rotate side schemes
            if card_img.size[0] > card_img.size[1]:
                card_img = card_img.rotate(90, expand=True)

            # Resize to card dimensions (at printable DPI)
            card_img = card_img.resize(size=(CARD_WIDTH_PX, CARD_HEIGHT_PX))
        except:
            print(f"ERROR: Could not render card ID {card_id}. A placeholder will be used.")
            # draw grey box
            card_img = Image.new("RGB",(CARD_WIDTH_PX, CARD_HEIGHT_PX), (225, 225, 225))

            # retrieve card name
            card_name = get_card_name_by_card_id(card_id)

            # add text to box
            txt_color = (0, 0, 0)
            txt_coords = (int(CARD_WIDTH_PX/2), int(CARD_HEIGHT_PX/2))
            font_path = os.path.expandvars("%SystemRoot%/Fonts/Arial.ttf")
            font = ImageFont.truetype(font_path, 60)
            ImageDraw.Draw(card_img).text(txt_coords, card_name, txt_color, font=font, anchor="mm") # anchor mm centers text

        card_imgs.append(card_img)
    
    # Combine the card images into grids
    numPagesToCreate = math.ceil(len(card_imgs)/CARDS_PER_PAGE)
    
    deck_imgs = []
    for page_num in range(numPagesToCreate):
        # create a blank image grid
        deck_img = Image.new('RGB', size=(PAGE_WIDTH_PX, PAGE_HEIGHT_PX), color=(255, 255, 255))

        # add card images to image grid
        for row_num in range(CARD_ROWS_PER_PAGE):
            for col_num in range(CARD_COLS_PER_PAGE):
                # Determine card position on the grid
                xCoord = PAGE_X_MARGIN_PX + col_num * CARD_WIDTH_PX
                yCoord = PAGE_Y_MARGIN_PX + row_num * CARD_HEIGHT_PX

                if row_num > 0:
                    yCoord += CARD_Y_SPACER_PX * (row_num)
                if col_num > 0:
                    xCoord += CARD_X_SPACER_PX * (col_num)

                # determine card image index
                card_img_idx = page_num * CARDS_PER_PAGE + CARD_ROWS_PER_PAGE * row_num + col_num

                # paste card image onto the grid
                if(card_img_idx < len(card_imgs)):
                    deck_img.paste(card_imgs[card_img_idx], box=(xCoord, yCoord))

        # Add image grid to list of deck images
        deck_imgs.append(deck_img)
    
    # Save the list of image grids as a PDF
    #timestamp =  time.time_ns()
    wipPdfName = f"{DECK_IMGS_FOLDER}/{deck_name}_wip.pdf"
    deck_imgs[0].save(wipPdfName, save_all=True, append_images=deck_imgs[1:])

    # Resize PDF (digital DPI is different than printable DPI, but image resolution is still saved)
    pdfReader = pypdf.PdfReader(wipPdfName)
    pdfWriter = pypdf.PdfWriter()

    if DEBUG_LOGS:
        print(f"PDF downscale percentage: {PDF_DOWNSCALE_PECENTAGE}")

    # iterate over all pages
    for page in pdfReader.pages:
        page.scale_by(PDF_DOWNSCALE_PECENTAGE)
        pdfWriter.add_page(page)

    finalPdfName = f"{DECK_IMGS_FOLDER}/{deck_name}.pdf"
    pdfWriter.write(finalPdfName)
    os.remove(wipPdfName)

    pdfPath = os.path.abspath(finalPdfName)
    print("\nCOMPLETE\n")
    print(f"Your printable deck is ready at: '{pdfPath}'")

### Main
# VS code/python debugger was adding weird stuff in print buffer, so flush it.
print('', flush=True) 

# retrieve decklist
deck_obj = get_card_ids_by_deck_id(DECK_ID)
card_ids = deck_obj["card_ids"]
deck_name = deck_obj["deck_name"]
card_slots = deck_obj["card_slots"]

# hide hero cards, if applicable
if HIDE_HERO_PACK:
    card_ids = hide_hero_pack(card_ids)

# download card images in deck
print("\nSTEP 2: Downloading card images\n")
for card_id in card_ids:
    download_card_img_by_card_id(card_id)

# create a decklist summary card image
# create_summary_card_img(card_slots, deck_name)
# TODO WIP

# assemble PDF from card images
create_deck_pdf_from_card_ids(card_ids, deck_name)

