from flask import Flask, render_template, redirect, url_for,request, jsonify
from elasticsearch import Elasticsearch,RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from flask_socketio import SocketIO, emit
import thread
import boto3
import keys
import json


application = Flask(__name__)
socketio = SocketIO(application)
index_name = 'tweet-index'

def search_tweets(es, keyword):
    if len(keyword) is not 0:
      res = es.search(size=10000, index="tweet-index", body={"query": {"query_string": {"query": keyword}}})
    else:
      res = es.search(size=10000,index='tweet-index')
    return res

def get_es_connection():
    AWS_ACCESS_KEY = keys.AWS_ACCESS_KEY
    AWS_SECRET_KEY = keys.AWS_SECRET_KEY

    host = keys.ESHOSTURL
    awsauth = AWS4Auth(AWS_ACCESS_KEY, AWS_SECRET_KEY, 'us-east-1', 'es')

    es = Elasticsearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    return es

@application.route('/',methods=['GET'])
def index(name = None):
    return render_template('index.html')

@application.route('/all', methods=['GET'])
def home(name = None):
    es = get_es_connection()
    result = es.search(size=10000, index=index_name)
    return render_template('all.html',data = result)

@application.route('/tweets/', methods=['GET'])
def tweets():
    es = get_es_connection()
    result = es.search(size = 10000,index = index_name)
    return jsonify(result)

@application.route('/search',methods=['POST'])
def search():
    keywords = request.form['search']
    es = get_es_connection()
    res = search_tweets(es,keywords)
    return render_template('all.html',data = res)

def confirmSubscription(token,topic_arn):
    sns = boto3.client('sns',aws_access_key_id= keys.AWS_ACCESS_KEY,
                        aws_secret_access_key = keys.AWS_SECRET_KEY,
                        region_name = 'us-east-1')
    try:
        response = sns.confirm_subscription(
            TopicArn=topic_arn,
            Token=token
        )
        print response
        # return jsonify({"status": "ok"})
    except:
        pass

def get_json_msg(data):
    dict={}
    l = data.strip().split("||")
    for item in l:
        sub = item.strip().split(":-")
        dict[sub[0]] = sub[1]
    return dict

@application.route('/notify',methods=['POST'])
def notify():
    data = {}
    data = request.get_data()
    print data
    json_data = json.loads(data)
    message_type = json_data["Type"]
    print message_type
    if message_type == 'Notification':
        message_data = json_data["Message"]
        json_msg = get_json_msg(message_data)
        lat = json_msg['lat']
        lng = json_msg['lng']
        sent = json_msg['sentiment']
        print json_msg
        es = get_es_connection()
        es.index(index='tweet-index', doc_type='tweets', id=json_msg["id"], body=json_msg)
        socketio.emit('newTweet',{'lat':lat,'lng':lng,'sentiment':sent})

    elif message_type == 'SubscriptionConfirmation':
        token = json_data["Token"]
        topic_arn = json_data["TopicArn"]
        confirmSubscription(token,topic_arn)
    return 'home'

if __name__ == '__main__':
    socketio.run(application)
