from elasticsearch import Elasticsearch,RequestsHttpConnection
import time
from tweepy import Stream, OAuthHandler
from tweepy.streaming import StreamListener
import json
from requests_aws4auth import AWS4Auth
import keys

#Keys
ACCESS_TOKEN = keys.TWITTER_ACCESS_TOKEN
ACCESS_SECRET = keys.TWITTER_ACCESS_SECRET
CONSUMER_KEY = keys.TWITTER_CONSUMER_KEY
CONSUMER_SECRET = keys.TWITTER_CONSUMER_SECRET
AWS_ACCESS_KEY = keys.AWS_ACCESS_KEY
AWS_SECRET_KEY = keys.AWS_SECRET_KEY

ES_HOST_URL = keys.ESHOSTURL

awsauth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, 'us-east-1', 'es')

es = Elasticsearch(
    hosts=[{'host': ES_HOST_URL, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)
print(es.info())


class listner(StreamListener):
    count = 0
    def on_data(self, raw_data):
        try:
            tweets_json = json.loads(raw_data)
            try:
                if('coordinates' in tweets_json):
                    if tweets_json["coordinates"] is not None:
                        lon = tweets_json["coordinates"]['coordinates'][0]
                        lat = tweets_json["coordinates"]['coordinates'][1]
                        text = tweets_json["text"]
                        text = text.encode(encoding='utf-8')
                        tweet_json = {
                            'tweet':text,
                            'lat':lat,
                            'lng':lon,
                            'id':tweets_json['id']
                        }
                        es.index(index='tweet-index',doc_type='tweets',id = tweet_json['id'],body=tweet_json)
                        print("done")

            except:
                return True
            return True
        except:
            print('error')
            time.sleep(1)

    def on_error(self, status_code):
        print(status_code)

oauth = OAuthHandler(CONSUMER_KEY,CONSUMER_SECRET)
oauth.set_access_token(ACCESS_TOKEN,ACCESS_SECRET)
while(True):
    try:
        twitterStream = Stream(oauth,listner())
        twitterStream.filter(languages=["en"],track=['i','u','in','is','was','where','you','me','have','with','buy','bought','product','india'])
    except:
        continue