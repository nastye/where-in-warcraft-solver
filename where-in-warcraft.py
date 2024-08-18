import json
import os
import pickle
import uuid
import logging

import requests

cache = {}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class Game():
    ENDPOINT='https://www.whereinwarcraft.net/endpoint.php'

    HEADERS = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    def __init__(self, cache_path, player_name, uid):
        self.score = 0
        self.cache_path = cache_path
        self.cache = {}
        self.player_name = player_name
        self.uid = uid

        self.session = requests.Session()

        self.load_cache()

    def start(self):
        logger.info('starting new game')
        r = self._request({'action': 'init', 'mode': 1})

        data = json.loads(r.text)

        self.token = data['token']
        self.location = data['location']
        self.finish = False

        logger.info(f'token: {self.token}')

    def guess(self):

        if self.location in self.cache and not self.finish:
            logger.debug('cache hit')
            lat = self.cache[self.location]['lat']
            lon = self.cache[self.location]['lon']
            mid = self.cache[self.location]['mid']
        else:
            logger.debug('cache miss')
            lat = 0
            lon = 0
            mid = 0

        r = self._request(
            {'action': 'guess',
             'lat': lat,
             'lng': lon,
             'mapID': mid,
             'token': self.token
            })

        data = json.loads(r.text)

        self.cache[self.location] = {'lat': data['lat'], 'lon': data['lng'], 'mid': data['mapID']}
        self.save_cache()
        self.score = data['score']

        # When you lose there's no location element.
        # When you complete the game the last location element is null
        if 'location' not in data or not data['location']:
            return False

        self.location = data['location']

        return True

    def submit(self):
        logger.info('submitting disabled')
        # r = self._request(
        #     {'action': 'submit',
        #      'name': self.player_name,
        #      'uid': self.uid,
        #      'token': self.token
        #     })

    def end_game(self):
        self.finish = True

    def load_cache(self):
        if os.path.exists(self.cache_path):
            self.cache = pickle.load(open(self.cache_path, 'rb'))

    def save_cache(self):
        pickle.dump(self.cache, open(self.cache_path, 'wb'))

    def _request(self, data):
        req_json = json.dumps(data)

        req = requests.Request(
            method='POST',
            url=Game.ENDPOINT,
            headers=Game.HEADERS,
            data=req_json)

        pr = self.session.prepare_request(req)


        resp = self.session.send(pr)

        logger.debug('---')
        logger.debug('request:')
        logger.debug(resp.request.body)
        logger.debug('response:')
        logger.debug(resp.text)

        return resp


def main():
    game = Game('cache.p', 'Skynet', uuid.uuid4().hex)
    logger.info(f'Loaded {len(game.cache)} items from cache')

    high_score = 0

    while(True):
        game.start()
        last_result = True
        while(last_result):
            try:
                last_result = game.guess()
            except KeyboardInterrupt:
                game.end_game()

        if (game.score > high_score):
            game.submit()
            high_score = game.score

        logger.info(f'Max Score: {high_score} Current Score: {game.score}. I have {len(game.cache)} items in the cache now')

        if game.finish:
            break

    game.save_cache()

if __name__ == '__main__':
    main()
