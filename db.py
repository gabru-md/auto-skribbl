try:
    from config import server_config
    config = server_config
except Exception:
    config = {
        'url': os.environ.get('MLAB_URL', '')
    }

client = pymongo.MongoClient(config['url'])
db = client.test