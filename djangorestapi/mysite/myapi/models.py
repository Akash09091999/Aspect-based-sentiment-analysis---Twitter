from django.db import models


# Create your models here.
class TweetMeta(models.Model):
    """Tweet Meta data"""
    id = models.AutoField(primary_key=True)
    twitter_id = models.BigIntegerField(default=0)
    tweet_timestamp = models.DateTimeField(null=True)
    tweet_hashtag = models.CharField(max_length=100)
    crawler_lastexecutiontime = models.DateTimeField(null=True)
    is_deleted = models.IntegerField(default=0)
    if_first = models.IntegerField(default=1)

    def __repr__(self):
        return "<TweetMeta(twitter_id={}, tweet_timestamp={}, tweet_hashtag='{}', crawler_lastexecutiontime={}, " \
               "is_deleted={}, if_first={})>".format(self.twitter_id, self.tweet_timestamp, self.tweet_hashtag, self.crawler_lastexecutiontime, self.is_deleted, self.if_first)


class AspectMeta(models.Model):
    """Aspect Meta data"""
    id = models.AutoField(primary_key=True)
    aspect = models.CharField(max_length=100)
    hashtag = models.ForeignKey(TweetMeta, on_delete=models.CASCADE)

    def __repr__(self):
        return "<AspectMeta(aspect={}, hashtag={})>".format(self.aspect, self.hashtag)


class DateWiseSentiment(models.Model):
    """Date wise sentiment for hashtag"""
    id = models.AutoField(primary_key=True)
    local_id = models.ForeignKey(TweetMeta, on_delete=models.CASCADE)
    date = models.DateField()
    sentiment_average = models.FloatField()

    def __repr__(self):
        return "<DateWiseSentiment(local_id={}, date={}, sentiment_average={})>". \
            format(self.local_id, self.date, self.sentiment_average)


class DateWiseSentimentForAspect(models.Model):
    """Date Wise sentiment for particular aspect on related hashtag"""
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    aspect = models.ForeignKey(AspectMeta, on_delete=models.CASCADE)
    sentiment_value = models.FloatField()