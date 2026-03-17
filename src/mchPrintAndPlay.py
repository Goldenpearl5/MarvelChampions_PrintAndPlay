# default modules
import os
import math
import re

# pip modules
from PIL import Image, ImageDraw, ImageFont
import pypdf
import pdfkit

# local modules
import config as config

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
    if(not os.path.exists(config.DECK_IMGS_FOLDER)):
        os.mkdir(config.DECK_IMGS_FOLDER)

    # Create a list of card images.
    card_imgs=[]
    for card_id in card_ids:
        card_img = None
        try:
            # load card image
            card_img = Image.open(f"{config.CARD_IMGS_FOLDER}/{card_id}.png").convert("RGB");

            # Rotate side schemes
            if card_img.size[0] > card_img.size[1]:
                card_img = card_img.rotate(90, expand=True)

            # Resize to card dimensions (at printable DPI)
            card_img = card_img.resize(size=(config.CARD_WIDTH_PX, config.CARD_HEIGHT_PX))
        except:
            print(f"ERROR: Could not render card ID {card_id}. A placeholder will be used.")
            # draw grey box
            card_img = Image.new("RGB",(config.CARD_WIDTH_PX, config.CARD_HEIGHT_PX), (225, 225, 225))

            # retrieve card name
            card_name = "Unknown"
            #card_name = get_card_name_by_card_id(card_id) # TODO offline mode

            # add text to box
            txt_color = (0, 0, 0)
            txt_coords = (int(config.CARD_WIDTH_PX/2), int(config.CARD_HEIGHT_PX/2))
            font_path = os.path.expandvars("%SystemRoot%/Fonts/Arial.ttf")
            font = ImageFont.truetype(font_path, 60)
            ImageDraw.Draw(card_img).text(txt_coords, card_name, txt_color, font=font, anchor="mm") # anchor mm centers text

        card_imgs.append(card_img)
    
    # Combine the card images into grids
    numPagesToCreate = math.ceil(len(card_imgs)/config.CARDS_PER_PAGE)
    
    deck_imgs = []
    for page_num in range(numPagesToCreate):
        # create a blank image grid
        deck_img = Image.new('RGB', size=(config.PAGE_WIDTH_PX, config.PAGE_HEIGHT_PX), color=(255, 255, 255))

        # add card images to image grid
        for row_num in range(config.CARD_ROWS_PER_PAGE):
            for col_num in range(config.CARD_COLS_PER_PAGE):
                # Determine card position on the grid
                xCoord = config.PAGE_X_MARGIN_PX + col_num * config.CARD_WIDTH_PX
                yCoord = config.PAGE_Y_MARGIN_PX + row_num * config.CARD_HEIGHT_PX

                if row_num > 0:
                    yCoord += config.CARD_Y_SPACER_PX * (row_num)
                if col_num > 0:
                    xCoord += config.CARD_X_SPACER_PX * (col_num)

                # determine card image index
                card_img_idx = page_num * config.CARDS_PER_PAGE + config.CARD_ROWS_PER_PAGE * row_num + col_num

                # paste card image onto the grid
                if(card_img_idx < len(card_imgs)):
                    deck_img.paste(card_imgs[card_img_idx], box=(xCoord, yCoord))

        # Add image grid to list of deck images
        deck_imgs.append(deck_img)
    
    # Save the list of image grids as a PDF
    #timestamp =  time.time_ns()

    # clean up filename
    deck_name_stripped = re.sub('\W+','', deck_name)

    wipPdfName = f"{config.DECK_IMGS_FOLDER}/{deck_name_stripped}_wip.pdf"
    deck_imgs[0].save(wipPdfName, save_all=True, append_images=deck_imgs[1:])

    # Resize PDF (digital DPI is different than printable DPI, but image resolution is still saved)
    pdfReader = pypdf.PdfReader(wipPdfName)
    pdfWriter = pypdf.PdfWriter()

    # iterate over all pages
    for page in pdfReader.pages:
        page.scale_by(config.PDF_DOWNSCALE_PECENTAGE)
        pdfWriter.add_page(page)

    finalPdfName = f"{config.DECK_IMGS_FOLDER}/{deck_name_stripped}.pdf"
    pdfWriter.write(finalPdfName)
    os.remove(wipPdfName)

    pdfPath = os.path.abspath(finalPdfName)
    print("\nCOMPLETE\n")
    print(f"Your printable deck is ready at: '{pdfPath}'")


