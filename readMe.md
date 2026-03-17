How to run:
1. Make sure python is installed.

2. Open a command prompt and run the following command:
> pip install -r requirements.txt

3. Open a command prompt and run
> python src/main.py


OPTIONAL STEPS:
Additional Arguments:
> -deckId <FILL_IN_DECK_ID>: specify deckID from marvelCDB.

> --hideHeroPack: removes hero-specific cards from the deck.

> --disableCardSpacers: removes whitespace between cards.

> --initOfflineMode: download ALL card images and info; allows offline use in future runs.

> --offlineMode: use a local files to generate the PDF. (.txt file and images)


e.g.
> python mchPrintAndPlay.py -deckId 60116

> python mchPrintAndPlay.py -deckId sampleDeck.txt --offlineMode

> python mchPrintAndPlay.py --disableCardSpacers --hideHeroPack


OFFLINE MODE:
Due to the frequent MarvelCDB outages, I added an offline mode. 
 a) Run with the --initOfflineMode flag when MarvelCDB is online. It will download all card images/data.
 b) Create a decklist .txt in the /decklists folder. An example file is enclosed. You can create this manually, or click the "download -> text file" button on MarvelCDB.
 c) Run with the --offlineMode flag at any time. You can specify the txt file name in the -deckId argument. Otherwise you will be prompted to enter it.

Upcoming features:
- Toggle Hi-Rez cards (sourced from https://drive.google.com/drive/folders/1FO7FRfJbqGsmAkfePhkzpmEqmW1-VwF2)
- Toggle Print and Bleed lines
- Compatibility with other card games? (e.g. LOTR and Arkham horror LCGs)