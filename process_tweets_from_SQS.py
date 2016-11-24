import traceback
# TODO:  Find sentiment of tweets and push in SNS
import boto3
import time
import json
import keys
from alchemyapi import AlchemyAPI
alchemyapi = AlchemyAPI()
count = 0;
sqs = boto3.resource('sqs')
sns = boto3.client('sns')
# sns.create_topic(Name='Tweets')
# sns = boto3.client('sns')
topiArn = 'arn:aws:sns:us-east-1:147607342157:tweets'
queue = sqs.get_queue_by_name(QueueName='tweets')
print(queue.url)

def find_sentiment(tweet, count=0):
    # TODO call alchamy api to find sentiment here
    if (count < 500):
        try:
            response = alchemyapi.sentiment("text", tweet)
            sentiment = response["docSentiment"]["type"]
            print("Sentiment: ", sentiment)
            if sentiment == 'positive':
                return "1"
            elif sentiment == 'negative':
                return "-1"
            return "0"
        except:
            return "0"
    return "0"

while True:
    m = queue.receive_messages()
    if(len(m)>0):
        raw_data = m[0].body
    else:
        continue
    raw_data = json.loads(raw_data)
    tweet = raw_data['tweet']
    sentiment = find_sentiment(tweet,count)
    count = count+1
    message = "tweet:-"+raw_data['tweet']+"||"+"lat:-"+str(raw_data['lat'])+"||"+"lng:-"+str(raw_data['lng'])\
              +"||"+"id:-"+str(raw_data['id'])+"||"+"sentiment:-"+str(sentiment)
    print(message)
    try:
        response = sns.publish(
            TopicArn=topiArn,
            Message=message,
            MessageStructure='String'
        )
        print("done")
        response = m[0].delete()
        print(response)
    except:
        print('error')
        pass
