import requests
import bs4
import json
import unicodedata
import sys
import logging

CONCURRENT = True
try:
    import concurrent.futures
except ImportError:
    CONCURRENT = False

UNICODE_DATA_URL = 'http://www.unicode.org/Public/UNIDATA/UnicodeData.txt'
EMOJI_DATA_URL = 'http://www.unicode.org/~scherer/emoji4unicode/snapshot/full.html'
TWITTER_URL_STRUCTURE = 'https://abs.twimg.com/emoji/v1/72x72/{twitter_id}.png'

logger = logging.getLogger(__name__)

def twitterize(codepoint):
    """Turn a codepoint string into an id as used by twitter's emoji image urls.

    E.g.:
      'U+00AE' => 'ae'
      'U+1F1EC U+1F1E7' => '1f1ec-1f1e7'

    Twitter emoji images urls: https://abs.twimg.com/emoji/v1/72x72/1f3c0.png
    """
    cps = codepoint.split(' ')
    return '-'.join([c.replace('U+','').lstrip('0').lower() for c in cps])


def is_valid_twitter_id(twitter_id):
    """Ensure a given id does indeed correspond to a twitter emoji image.

    Side effect: Http request.
    Twitter image url: https://abs.twimg.com/emoji/v1/72x72/<twitter_id>.png
    """
    return requests.get(TWITTER_URL_STRUCTURE.format(twitter_id=twitter_id)).ok


def get_raw_emoji_data():
    """Relevant emoji data pulled from the EMOJI_DATA_URL

    Side effect: Http request.
    Returns: list of emoji data dicts e.g. [
      {
        'emoji-id': 'e-7D6'
        'name': 'BASKETBALL AND HOOP'
        'codepoint': 'U+1F3C0'
      },
      ...
    ]
    """
    # Get the page and make soup from the html.
    soup = bs4.BeautifulSoup(requests.get(EMOJI_DATA_URL).text)
    # All content we need is stored in <tr> elements.
    trs = soup.find_all('tr')
    # Seems only <tr> with an 'id' and without a 'class' attribute are relevant.
    good_trs = [tr for tr in trs if 'id' in tr.attrs and 'class' not in tr.attrs]

    def extract_codepoint(tr):
        elm = list(tr.find_all('td')[1].find('br').children)[0]
        if hasattr(elm, 'text'):
            elm = elm.text
        return elm.format()

    # Construct a list of dicts containing the raw data we want
    emojis = [{
            'emoji-id': tr.attrs['id'],
            'name': list(tr.find_all('td')[2].children)[0],
            'codepoint': extract_codepoint(tr)
    } for tr in good_trs]
    return emojis


def get_full_codepoint_name_dict():
    """Get a dict of unicode 'codepoint': 'name' from the official source

    Side effect: Http request.
    Returns: dict of unicode name data e.g.
      {
        '0027': 'APOSTROPHE',
        ...
      }
    """
    # Not as pythonic as a dictionary comprehension cause we want exception
    # handling.
    results = {}
    for line in requests.get(UNICODE_DATA_URL).text.split('\n'):
        try:
            results[line.split(';')[0].upper()] = line.split(';')[1]
        except IndexError:
            pass
    return results


def raw_emoji_data_to_emoji_dict(raw_emoji_data, unicode_data):
    """Convert our raw emoji data to a dictionary keyed by the (python unicode)
    string represented by that emoji's codepoints.

    E.g:
    [
      {
        'emoji-id': 'e-000',
        'codepoint': 'U+2600',
        'name': 'BLACK SUN WITH RAYS',
        'twitter-id': '2600'
      },
      {
        'emoji-id': 'e-4ED',
        'codepoint': 'U+1F1E8 U+1F1F3',
        'name': 'REGIONAL INDICATOR SYMBOL LETTERS CN',
        'twitter-id': '1f1e8-1f1f3'
      }
    ]

    ==>

    {
      u'\u2600': {
        'emoji-id': 'e-000',
        'codepoint': 'U+2600',
        'name': 'BLACK SUN WITH RAYS',
        'twitter-id': '2600'
      },
      u'\ud83c\udde8\ud83c\uddf3': {
        'emoji-id': 'e-4ED',
        'codepoint': 'U+1F1E8 U+1F1F3',
        'name': 'REGIONAL INDICATOR SYMBOL LETTERS CN',
        'twitter-id': '1f1e8-1f1f3'
      }
    }
    """
    def encode_codepoints(codepoint):
        names = [
            unicode_data[cp.replace('U+','').upper()]
            for cp in codepoint.split(' ')
        ]
        return ''.join([unicodedata.lookup(name) for name in names])

    return {encode_codepoints(e['codepoint']): e for e in raw_emoji_data}


def main():
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stderr))

    logger.info(' EMOJI DATA CREATOR '.center(80, '='))

    logger.info('Getting and parsing emoji data')

    raw_data = get_raw_emoji_data()

    logger.info(''.center(80, '-'))
    logger.info('Creating twitter ids')

    [e.update({'twitter-id': twitterize(e['codepoint'])}) for e in raw_data]

    logger.info(''.center(80, '-'))
    logger.info('Checking that twitter ids are valid...')

    bad_twitter_ids = set()

    def check_with_twitter(twitter_id):
        if is_valid_twitter_id(twitter_id):
            logger.info('%s (GOOD)' % twitter_id)
        else:
            bad_twitter_ids.add(twitter_id)
            logger.info('%s (BAD)' % twitter_id)

    if CONCURRENT:
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(check_with_twitter, emoji['twitter-id'])
                       for emoji in raw_data]
        concurrent.futures.wait(futures)
    else:
        [check_with_twitter(emoji['twitter-id']) for emoji in raw_data]

    logger.info(''.center(80, '-'))
    logger.info('Removing %s bad twitter-ids from data' % len(bad_twitter_ids))
    raw_data = [e for e in raw_data if e['twitter-id'] not in bad_twitter_ids]

    logger.info(''.center(80, '-'))
    logger.info('Getting and parsing unicode data')
    unicode_data = get_full_codepoint_name_dict()

    logger.info(''.center(80, '-'))
    logger.info('Creating final emoji dict')
    emoji_dict = raw_emoji_data_to_emoji_dict(raw_data, unicode_data)

    json.dump(emoji_dict, sys.stdout, indent=2)

    logger.info(' DONE '.center(80, '='))

if __name__ == '__main__':
    main()
