try:
    from config import server_config
    config = server_config
except Exception:
    import os
    config = {
        'url': os.environ.get('MLAB_URL', '')
    }

import pymongo

client = pymongo.MongoClient(config['url'])
db = client.test