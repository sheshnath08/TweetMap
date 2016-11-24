import traceback

import boto3
import time
from tweepy import Stream, OAuthHandler
from tweepy.streaming import StreamListener
import json
import keys
count = 0
sqs = boto3.resource('sqs',
                     aws_access_key_id= keys.AWS_ACCESS_KEY,
                     aws_secret_access_key = keys.AWS_SECRET_KEY,
                     )
ACCESS_TOKEN = keys.TWITTER_ACCESS_TOKEN
ACCESS_SECRET = keys.TWITTER_ACCESS_SECRET
CONSUMER_KEY = keys.TWITTER_CONSUMER_KEY
CONSUMER_SECRET = keys.TWITTER_CONSUMER_SECRET
# Get the queue. This returns an SQS.Queue instance
try:
    queue = sqs.get_queue_by_name(QueueName='tweets')
except:
    queue = sqs.create_queue(QueueName = 'tweets')
print(queue.url)

class listner(StreamListener):
    def on_data(self, raw_data):
        global count
        try:
            tweets_json = json.loads(raw_data)
            try:
                if('coordinates' in tweets_json):
                    if tweets_json["coordinates"] is not None:
                        lon = tweets_json["coordinates"]['coordinates'][0]
                        lat = tweets_json["coordinates"]['coordinates'][1]
                        text = tweets_json["text"]
                        # text = text.encode(encoding='utf-8')
                        tweet_json = {
                            "tweet":text,
                            "lat":lat,
                            "lng":lon,
                            "id":tweets_json['id']
                        }
                        json_dump = json.dumps(tweet_json)
                        if(count<200):
                            res = queue.send_message(MessageBody=str(json_dump))
                            count = count+1
                            print(res)
                        else:
                            print(count)
            except:
                print('error')
                return True
            return True
        except:
            print('error')
            traceback.print_exc()
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