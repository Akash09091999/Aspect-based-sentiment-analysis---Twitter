import psycopg2
from pymongo import MongoClient
from datetime import datetime, timedelta
from sanlpbert import BertAnalyzer

bert = BertAnalyzer()

client = MongoClient('mongodb://localhost:27017')
db = client.TweetScraper
tweets = db.tweet

try:
    conn = psycopg2.connect(host="localhost", database="tweetdb", user="postgres", password="postgres")
except:
    print("DB Connection Failed")

cursor = conn.cursor()

cursor.execute("SELECT id FROM myapi_tweetmeta")
hashtag_values = cursor.fetchall()

for every_hashtag_id in hashtag_values:
    prev_date = datetime.strftime(datetime.now(), '%Y-%m-%d')
    data = list(tweets.find({"local_ID":every_hashtag_id[0],"found_relevance" : 0},{"sentiment":1,"text":1, "_id":0}))
    print("----",data)
    text_list = [tweet['text'] for tweet in data]
    sentiment_list = [tweet['sentiment'] for tweet in data]
    print('sentiment_list',sentiment_list)
    cursor.execute("SELECT aspect,id FROM myapi_aspectmeta WHERE hashtag_id={}".format(every_hashtag_id[0]))
    aspects = cursor.fetchall()

    if len(text_list) and len(sentiment_list) and len(aspects):
        for aspect in aspects:
            print(aspect)
            print(aspect[1])
            print("aspect finding relavance : " + aspect[0])
            aspect_list = [aspect[0]] * len(text_list)
            relavance_result = bert.getRelavance(text_list, aspect_list)
            aspect_sentiment, relavent_tweets = 0,0
            for i in range(0,len(sentiment_list)):
                if relavance_result[i][2] == 'Related':
                    aspect_sentiment += sentiment_list[i]
                    relavent_tweets += 1
            if relavent_tweets:
                aspect_sentiment /= relavent_tweets
            cursor.execute("INSERT INTO myapi_datewisesentimentforaspect (sentiment_value,aspect_id,date) VALUES (%s,%s,%s)",(aspect_sentiment, aspect[1], prev_date))
            conn.commit()


# cursor.execute("INSERT INTO myapi_datewisesentimentforaspect (sentiment_value,aspect_id,date) VALUES (%s,%s,%s)",(aspect[0], every_hashtag_id[0], prev_date))
            
            
    

