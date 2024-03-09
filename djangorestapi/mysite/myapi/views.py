# import TweetScraper
# from TweetScraper.TweetScraper.spiders import TweetCrawler
from msilib.schema import Error
import uuid
from django.shortcuts import render
from rest_framework import viewsets, response, status,views
from rest_framework.decorators import action
from django.http import Http404, JsonResponse
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from django.db.models import Avg
import requests
from .serializers import TweetMetaSerializer
from .models import TweetMeta, DateWiseSentiment, AspectMeta, DateWiseSentimentForAspect
import pytz
from pymongo import MongoClient
from datetime import datetime, timedelta
from myapi import utils as api_utils
import time
client = MongoClient('localhost', 27017)

db = client['TweetScraper']

tweets = db.tweet


def check_hashtag(hashtag):
    if hashtag[0] == '#':
        return hashtag
    else:
        return '#' + hashtag

def remove_hash(data):
    ans = []
    for x in data:
        m = x.replace("#","");
        ans.append(m)
    return ans
# Create your views here.


class TweetMetaViewSet(viewsets.ViewSet):
    queryset = TweetMeta.objects.all().order_by('id')
    serializer_class = TweetMetaSerializer

    @action(detail=True, methods=["post"])
    def add_hashtag_aspect(self, request):
        entity_present = True
        hashtag = request.data['hashtag'].strip().lower()
        hashtag = check_hashtag(hashtag)
        aspects = request.data['aspects'].strip().lower()
        if not hashtag:
            return response.Response(data={"Message": "Enter Valid Hashtag"}, status=status.HTTP_400_BAD_REQUEST)
        if not aspects:
            return response.Response(data={"Message": "Enter Valid Aspect/s"}, status=status.HTTP_400_BAD_REQUEST)
        aspect_list = aspects.split(',')
        aspect_list_clean = []
        for aspect in aspect_list:
            aspect_list_clean.append(aspect.strip())
        print(aspect_list_clean)
        if not TweetMeta.objects.filter(tweet_hashtag=hashtag, is_deleted=0).all():
            new_hashtag_entry = TweetMeta(twitter_id=0, tweet_hashtag=hashtag, tweet_timestamp=datetime(1999, 4, 16, 12, 10, 0))
            new_hashtag_entry.save()
            print(new_hashtag_entry.id)
            for aspect in aspect_list_clean:
                new_aspect_entry = AspectMeta(aspect=aspect, hashtag=new_hashtag_entry)
                new_aspect_entry.save()
            return response.Response(data={"Message": "Hashtag " + hashtag + " added."})
        else:
            hashtag_entry = TweetMeta.objects.get(tweet_hashtag=hashtag)
            for aspect in aspect_list_clean:
                if not AspectMeta.objects.filter(aspect=aspect, hashtag=hashtag_entry):
                    new_aspect_entry = AspectMeta(aspect=aspect, hashtag=hashtag_entry)
                    new_aspect_entry.save()
                    entity_present = False
            if entity_present:
                return response.Response(data={"Message": "Aspect/s are already added"}, status=status.HTTP_409_CONFLICT)
            else:
                return response.Response(data={"Message": "Aspect/s {} added".format(aspect_list_clean)})

    @action(detail=True, methods=["post"])
    def delete_hashtag(self, request):
        hashtag = request.data['hashtag'].strip().lower()
        hashtag = check_hashtag(hashtag)
        if TweetMeta.objects.filter(tweet_hashtag=hashtag, is_deleted=0).all():
            # new_entry = TweetMeta(TwitterId=0, TweetHashTag=hashtag)
            # new_entry.save()
            # print(new_entry.id)

            entry = TweetMeta.objects.get(tweet_hashtag=hashtag)
            entry.is_deleted = 1
            entry.save()
            return response.Response(data={"Message": "Hashtag " + hashtag + " deleted."})
        else:
            return response.Response(data={"Message": "Hashtag does not exist."})

    @action(detail=True, methods=["get"])
    def get_hashtags(self, request):
        hashtags = TweetMeta.objects.filter(is_deleted=0).all().values('tweet_hashtag')
        hashtag_list = [hashtag['tweet_hashtag'] for hashtag in hashtags]
        print(hashtag_list)
        data = {'hashtag_list': hashtag_list}
        return JsonResponse(data)

    @action(detail=True, methods=["get"])
    def get_sentiment(self, request):
        hashtag = request.query_params.get('hashtag').strip().lower()
        hashtag = check_hashtag(hashtag)
        print(hashtag)
        if TweetMeta.objects.filter(tweet_hashtag=hashtag, is_deleted=0):
            hashtag_obj = TweetMeta.objects.get(tweet_hashtag=hashtag)
            query_set = DateWiseSentiment.objects.filter(local_id=hashtag_obj.id).all().order_by('-date').values('date', 'sentiment_average')[:7]
            day_wise_sentiment = {}
            for every_value in query_set:
                day_wise_sentiment[datetime.strftime(every_value['date'], '%Y-%m-%d')] = every_value['sentiment_average']
            print(day_wise_sentiment)
            sentiment_average = DateWiseSentiment.objects.filter(local_id=hashtag_obj.id).all().aggregate(Avg('sentiment_average'))
            aspects_queryset = AspectMeta.objects.filter(hashtag=hashtag_obj).all()
            aspect_sentiment_list = {}
            for aspect_obj in aspects_queryset:
                print(aspect_obj.aspect)
                aspect_sentiment_queryset = DateWiseSentimentForAspect.objects.filter(aspect=aspect_obj).all().order_by('-date').values('date','sentiment_value')[:7]
                print("++++++++++++++++++++++++++++++++++++++++++")
                print(aspect_sentiment_queryset)
                aspect_sentiments = {}
                for every_aspect_value in aspect_sentiment_queryset:
                    aspect_sentiments[datetime.strftime(every_aspect_value['date'], '%Y-%m-%d')] = every_aspect_value['sentiment_value']
                aspect_sentiment_list[aspect_obj.aspect] = aspect_sentiments

            data = {'day_wise_sentiment': day_wise_sentiment,
                    'sentiment_average': sentiment_average["sentiment_average__avg"],
                    'aspect_sentiment': aspect_sentiment_list}
            return JsonResponse(data)
        else:
            return response.Response(data={"Message": "Hashtag does not exist."})

    @action(detail=True, methods=["get"])
    def get_range_sentiment(self, request):
        # extract hashtag from query params
        hashtag = request.query_params.get('hashtag').strip().lower()
        hashtag = check_hashtag(hashtag)
        if not hashtag:
            return response.Response(data={"Message": "Enter Valid Hashtag"}, status=status.HTTP_400_BAD_REQUEST)

        # extract start-end range from query params
        start = request.query_params.get('start').strip()
        end = request.query_params.get('end').strip()
        if not start or not end:
            return response.Response(data={"Message": "Enter Valid range"}, status=status.HTTP_400_BAD_REQUEST)
        start = datetime.strptime(start, '%Y-%m-%d')
        end = datetime.strptime(end, '%Y-%m-%d')

        if TweetMeta.objects.filter(tweet_hashtag=hashtag, is_deleted=0):
            hashtag_id = TweetMeta.objects.get(tweet_hashtag=hashtag).id
            if DateWiseSentiment.objects.filter(local_id=hashtag_id, date=end) and DateWiseSentiment.objects.filter(local_id=hashtag_id, date=start):
                sentiment_average = DateWiseSentiment.objects.filter(local_id=hashtag_id, date__range=[start, end]).all().aggregate(Avg('sentiment_average'))
                print(sentiment_average)
                query_set = DateWiseSentiment.objects.filter(local_id=hashtag_id, date__range=[start, end]).all().order_by('-date').values('date', 'sentiment_average')
                day_wise_sentiment = {}
                for every_value in query_set:
                    day_wise_sentiment[datetime.strftime(every_value['date'], '%Y-%m-%d')] = every_value[
                        'sentiment_average']
                print(day_wise_sentiment)
                data = {'day_wise_sentiment': day_wise_sentiment,
                        'sentiment_average': sentiment_average["sentiment_average__avg"]}
                return JsonResponse(data)
            else:
                return response.Response(data={"Message": "Enter a proper range"})
        else:
            return response.Response(data={"Message": "Hashtag does not exist."})




class FetchTweets(viewsets.ViewSet):
    @action(detail=True, methods=["post"])
    def fetch_recent_tweets(self,request):
        
        try:
            data = request.data
            if not data['hashtag']:
                return Http404
            print("---------------",data['hashtag'])
            local_id= ''
            tweetmeta = TweetMeta.objects.filter(tweet_hashtag__contains=data['hashtag']).last()
            if tweetmeta:
                print("====================",tweetmeta.id)
                local_id=tweetmeta.id
            
            url = "https://api.twitter.com/2/tweets/search/recent?query=%23"+data['hashtag'].strip().lower()

            payload={}
            headers = {
            'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAAICrigEAAAAAuH63xPk5ealJLkdWwnFInmm4RuQ%3DckVRCy8q0fs96FEuEwN5q9QJy7mt880uSjKw6kkaTMh5s2scQO',
            'Cookie': 'guest_id=v1%3A166702462652005042; guest_id_ads=v1%3A166702462652005042; guest_id_marketing=v1%3A166702462652005042; personalization_id="v1_4UHjBsf5sedOPamb78wLkg=="'
            }

            res = requests.request("GET", url, headers=headers, data=payload)

            # print(res.text)
            actual_res = res.json()
            
            tweets_data = actual_res['data']
            for i in tweets_data:   
                print(i)
                i['id'] = uuid.uuid4()
                i['sentiment'] = 0
                i['found_relevance'] = 0
                i['local_ID']=local_id
                i['query']=data['hashtag'].strip().lower()
                i['date']= datetime.strftime(datetime.now() , '%Y-%m-%d' )
                result = tweets.insert_one(i)
                print(result.inserted_id)
            return response.Response(data=res.json())
        except Exception as e:
            print(e)
            return response.Response(data="Error occured ")
    
    
    
  
    
    
    @action(detail=True, methods=["get"])
    def daily_search(self,request):
        try:
            
            hashtags = TweetMeta.objects.filter(is_deleted=0).all().values('tweet_hashtag')
            hashtag_list = [hashtag['tweet_hashtag'] for hashtag in hashtags]
            print(hashtag_list)
            
            pure_hashtags = remove_hash(hashtag_list)
            print(pure_hashtags)
            response_arr_obj = []
            for hash in pure_hashtags:
                
                if not hash:
                    return Http404
                print("---------------",hash)
                local_id= ''
                tweetmeta = TweetMeta.objects.filter(tweet_hashtag__contains=hash).last()
                if tweetmeta:
                    print("====================",tweetmeta.id)
                    local_id=tweetmeta.id
                
                url = "https://api.twitter.com/2/tweets/search/recent?query=%23"+hash.strip().lower()

                payload={}
                headers = {
                'Authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAAICrigEAAAAAuH63xPk5ealJLkdWwnFInmm4RuQ%3DckVRCy8q0fs96FEuEwN5q9QJy7mt880uSjKw6kkaTMh5s2scQO',
                'Cookie': 'guest_id=v1%3A166702462652005042; guest_id_ads=v1%3A166702462652005042; guest_id_marketing=v1%3A166702462652005042; personalization_id="v1_4UHjBsf5sedOPamb78wLkg=="'
                }

                res = requests.request("GET", url, headers=headers, data=payload)

                # print(res.text)
                actual_res = res.json()
                
                tweets_data = actual_res['data']
                for i in tweets_data:   
                    print(i)
                    i['id'] = uuid.uuid4()
                    i['sentiment'] = 0
                    i['found_relevance'] = 0
                    i['local_ID']=local_id
                    i['query']=hash.strip().lower()
                    i['date']= datetime.strftime(datetime.now() , '%Y-%m-%d' )
                    result = tweets.insert_one(i)
                    print(result.inserted_id)
                response_arr_obj.append(res.json())
                
            return response.Response(data=response_arr_obj)
        except Exception as e:
            print(e)
            return response.Response(data="Error occured ",status=500)