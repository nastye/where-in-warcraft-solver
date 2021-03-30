import json
import os
import pickle
import requests
import uuid

cache = {}

class Game():
    ENDPOINT='http://www.kruithne.net/where-in-warcraft/endpoint.php'

    HEADERS = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    def __init__(self, cache_path, player_name, uid):
        self.score = 0
        self.cache_path = cache_path
        self.cache = {}
        self.player_name = player_name
        self.uid = uid

        self.load_cache()

    def start(self):
        r = self._request({'action': 'init', 'mode': 2})

        data = json.loads(r.text)

        self.token = data['token']
        self.location = data['location']
        self.finish = False

    def guess(self, lat, lon):

        if self.location in self.cache and not self.finish:
            lat = self.cache[self.location]['lat']
            lon = self.cache[self.location]['lon']

        r = self._request(
            {'action': 'guess',
             'lat': lat,
             'lng': lon,
             'token': self.token
            })

        data = json.loads(r.text)

        self.cache[self.location] = {'lat': data['lat'], 'lon': data['lng']}
        self.score = data['score']

        # When you lose there's no location element.
        # When you complete the game the last location element is null
        if 'location' not in data or not data['location']:
            return False

        self.location = data['location']

        return True

    def submit(self):
        r = self._request(
            {'action': 'submit',
             'name': self.player_name,
             'uid': self.uid,
             'token': self.token
            })

    def end_game(self):
        self.finish = True

    def load_cache(self):
        if os.path.exists(self.cache_path):
            self.cache = pickle.load(open(self.cache_path, 'rb'))

    def save_cache(self):
        pickle.dump(self.cache, open(self.cache_path, 'wb'))

    def _request(self, data):
        r = requests.post(
            Game.ENDPOINT,
            data=json.dumps(data),
            headers=Game.HEADERS)

        print(r.text)

        return r


def main():
    game = Game('cache.p', 'Skynet', uuid.uuid4().hex)
    print(f'Loaded {len(game.cache)} items from cache')

    high_score = 0

    while(True):
        game.start()
        last_result = True
        while(last_result):
            try:
                last_result = game.guess(0, 0)
            except KeyboardInterrupt:
                game.end_game()

        if (game.score > high_score):
            game.submit()
            high_score = game.score

        print(f'Max Score: {high_score} Current Score: {game.score}. I have {len(game.cache)} items in the cache now')

        if game.finish:
            break

    game.save_cache()

if __name__ == '__main__':
    main()
