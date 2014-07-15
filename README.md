emoji-data-creator
==================

Create a JSON object with some useful emoji data.  Made for use with [angular-emojify](https://github.com/code/angular-emojify).

Parses emoji data from http://www.unicode.org/~scherer/emoji4unicode/snapshot/full.html and outputs text looking like:

    {
      ...
      "\ud83c\uddea\ud83c\uddf8": {
        "codepoint": "U+1F1EA U+1F1F8",
        "name": "REGIONAL INDICATOR SYMBOL LETTERS ES",
        "twitter-id": "1f1ea-1f1f8",
        "emoji-id": "e-4EB"
      },
      "\ud83c\udf59": {
        "codepoint": "U+1F359",
        "name": "RICE BALL",
        "twitter-id": "1f359",
        "emoji-id": "e-961"
      },
      "\ud83d\udcd8": {
        "codepoint": "U+1F4D8",
        "name": "BLUE BOOK",
        "twitter-id": "1f4d8",
        "emoji-id": "e-500"
      },
      "\ud83d\ude47": {
        "codepoint": "U+1F647",
        "name": "PERSON BOWING DEEPLY",
        "twitter-id": "1f647",
        "emoji-id": "e-353"
      },
      ...
    }

All data is verified against twitter emoji images (e.g. https://abs.twimg.com/emoji/v1/72x72/1f647.png)

Usage
-----

Make a (preferably python3.3+ virtualenv) then

    pip install -r requirements.txt
    python ./emoji_data_creator.py > emoji-data.json
