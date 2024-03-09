from datetime import datetime,timedelta
import tensorflow as tf
from tensorflow import keras

from tensorflow.keras.models import load_model
from keras_preprocessing.sequence import pad_sequences
import pickle

from pymongo import MongoClient

print("Step 1")
client = MongoClient('mongodb://localhost:27017')
db = client.TweetScraper
tweets = db.tweet

with open('tokenizer.pickle', 'rb') as handle:
    tokenizer = pickle.load(handle)
loaded_CNN_model = load_model('avi-CNN_best_weights.02-0.8329.hdf5')
print("Step 2")

def predict_sentiment(text):
    pre_val = tokenizer.texts_to_sequences(text)
    pre_val_seq = pad_sequences(pre_val, maxlen=400)
    return loaded_CNN_model.predict(pre_val_seq)

print("Step 3")

for post in tweets.find({'sentiment': 0}):
    print('step 4')
    arr = [post['text']]
    print("==============",arr)
    sentiment_value = predict_sentiment(arr)
    print("sentiment_value",sentiment_value)
    query = {'id': post['id']}
    new_value = {"$set": {"sentiment": float(sentiment_value[0][0])}}
    print(new_value)
    tweets.update_one(query, new_value)


# x = predict_sentiment(['New movie','modi is a great person','pappu is a rahul',' you are cool'])

# print("Ans :" ,x)


# for post in tweets.find():
#     # print(post)
#     query = {'id': post['id']}
#     new_value = {"$set": {"date":  datetime.strftime(datetime.now() - timedelta(1) , '%Y-%m-%d' )}} 
#     tweets.update_one(query, new_value)