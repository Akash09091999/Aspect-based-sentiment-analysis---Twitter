from rest_framework import serializers

from .models import TweetMeta


class TweetMetaSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TweetMeta
        fields = ('TwitterId', 'TweetTimeStamp', 'TweetHashTag', 'crawlerLastExecutionTime')
