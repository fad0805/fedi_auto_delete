import logging.config
import time
from parse import compile
import os
import re
import threading

import mastodon as mstdn
from mastodon import Mastodon
from mastodon import StreamListener

API_BASE_URL = os.getenv('API_BASE_URL')
CLIENT_KEY = os.getenv('CLIENT_KEY')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')

logger = logging.getLogger(__name__)


def delete_status(api: Mastodon, delay:int, status_id: str):
    time.sleep(delay)
    try:
        api.status_delete(status_id)
        logger.info(f"Deleted {status_id}")
    except Exception as e:
        logger.error(e)

class MyListener(StreamListener):
    def __init__(self, api: Mastodon):
        super().__init__()
        self.api = api
        self.logger = logging.getLogger('deleteit')
        self.me = self.api.account_verify_credentials()
        self.logger.info(f'I am {self.me["acct"]}')

    def on_update(self, status):
        if status['account']['id'] == self.me['id'] and "/tags/delete" in status['content']:
            hashtag = compile('<p>{}<a href="https://qdon.space/tags/delete" class="mention hashtag" rel="tag">#<span>delete</span></a> {}</p>')
            content = hashtag.parse(status['content'])[0]
            delay_str = hashtag.parse(status['content'])[1]
            logger.info(f"Deleting {content}")

            count = 0
            delay = 0

            pattern = r'(\d+d)?\s*(\d+h)?\s*(\d+m)?\s*(\d+s)?'
            match = re.match(pattern, delay_str)
            if not match:
                return
            else:
                for unit in match.groups():
                    if unit is None:
                        continue
                    elif "s" in unit:
                        count = 1
                    elif "m" in unit:
                        count = 60
                    elif "h" in unit:
                        count = 60 * 60
                    elif "d" in unit:
                        count = 60 * 60 * 24
                    delay += int(unit[:-1]) * count

            thread = threading.Thread(target=delete_status, args=(self.api, delay, status['id']))
            thread.start()


def set_logger():
    logging.config.fileConfig('logging.conf')


def make_streaming():
    try:
        api = Mastodon(
            api_base_url=API_BASE_URL,
            client_id=CLIENT_KEY,
            client_secret=CLIENT_SECRET,
            access_token=ACCESS_TOKEN,
        )
        api.stream_user(MyListener(api), reconnect_async=True)
    except Exception as e:
        logger.error(e)


def main():
    set_logger()

    logger.info("Start DeleteIt")
    make_streaming()


if __name__ == "__main__":
    while True:
        try:
            main()
        except mstdn.MastodonNetworkError:
            pass
        except Exception as e:
            print(e)

