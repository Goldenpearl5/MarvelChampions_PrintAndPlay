How to run:
1. Make sure python is installed.

2. Open a command prompt and run the following command:
> pip install -r requirements.txt

3. Open a command prompt and run
> python mchPrintAndPlay.py -deckId <FILL_IN_DECK_ID>"

e.g. 

> python mchPrintAndPlay.py -deckId 60116


4. Additional Arguments:
> --disableCardSpacers --hideHeroPack

e.g.

> python mchPrintAndPlay.py -deckId 60116 --disableCardSpacers

> python mchPrintAndPlay.py -deckId 60116 --hideHeroPack

--hideHeroPack: removes hero-specific cards from the deck.

--disableCardSpacers: removes whitespace between cards.


Upcoming features:
- Toggle Hi-Rez cards (sourced from https://drive.google.com/drive/folders/1FO7FRfJbqGsmAkfePhkzpmEqmW1-VwF2)
- Toggle Print and Bleed lines
- Compatibility with other card games? (e.g. LOTR and Arkham horror LCGs)