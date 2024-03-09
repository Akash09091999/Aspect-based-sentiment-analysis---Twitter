from django.urls import include, path
from . import views

tweetMeta_post = views.TweetMetaViewSet.as_view({
    'post': 'add_hashtag_aspect'
})
tweetMeta_delete = views.TweetMetaViewSet.as_view({
    'post': 'delete_hashtag'
})
tweetMeta_get_sentiment = views.TweetMetaViewSet.as_view({
    'get': 'get_sentiment'
})
tweetMeta_get_range_sentiment = views.TweetMetaViewSet.as_view({
    'get': 'get_range_sentiment'
})
tweetMeta_get_hashtags = views.TweetMetaViewSet.as_view({
    'get': 'get_hashtags'
})

fetch_recent_tweets = views.FetchTweets.as_view({
    'post' : 'fetch_recent_tweets'
})

daily_search = views.FetchTweets.as_view({
    'get' : 'daily_search'
})
# Wire up o
# ur API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    #path('', include(router.urls)),
    path('add_hashtag/', tweetMeta_post, name='tweetMeta'),
    path('delete_hashtag/',tweetMeta_delete,name='tweetMeta'),
    path('get-sentiment/', tweetMeta_get_sentiment, name='tweetMeta'),
    path('get-range-sentiment/', tweetMeta_get_range_sentiment, name='tweetMeta'),
    path('get-hashtags/', tweetMeta_get_hashtags, name='tweetMeta'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path(
        "fetch-tweets/",
        fetch_recent_tweets,
        name="fetchtweets",
    ),
    
    path(
        "daily-search/",
        daily_search,
        name="daily_search",
    ),
    
    
]
