from pymongo import MongoClient
from datetime import datetime, timedelta
import psycopg2, pytz


# mongodb connection
client = MongoClient('mongodb://localhost:27017')
db = client.TweetScraper

try:
    conn = psycopg2.connect(host="localhost", database="tweetdb", user="postgres", password="postgres")
except:
    print("DB Connection Failed")

cursor = conn.cursor()

# collection which are needed
tweets = db.tweet


# query to find average those have previous date and same local_ID
query = [{'$match': {'date': datetime.strftime(datetime.now()  , '%Y-%m-%d' )}}, {'$group': {'_id': {'local_ID': '$local_ID', 'date': '$date'}, 'sentimentAverage': {'$avg': '$sentiment'}}}]
# query = [{'$group': {'_id': {'local_ID': '$local_ID', 'date': '$date'}, 'sentimentAverage': {'$avg': '$sentiment'}}}]


print(query)
# inserting every document into db
avg = tweets.aggregate(query)


print(avg)
for every in avg:
    print(every)
    # entry = DateWiseSentiment(local_ID=every['_id']['local_ID'], date=every['_id']['date'], sentimentAverage=every['sentimentAverage'])
    if 'date' in every['_id'].keys():
        date = datetime.strptime(every['_id']['date'], '%Y-%m-%d')
        
        if 'local_ID' in every['_id'].keys():
            if every['_id']['local_ID']:
                
                print("every['sentimentAverage']",every['sentimentAverage'])
                cursor.execute("INSERT INTO myapi_datewisesentiment (local_id_id, date, sentiment_average) VALUES (%s, %s, %s)", (every['_id']['local_ID'], date, every['sentimentAverage']))
                conn.commit()
        else:
            print("no local_ID found")
    else:
        print("No date found")