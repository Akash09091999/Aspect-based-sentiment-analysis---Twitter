from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, BigInteger

Base = declarative_base()


class TweetMeta(Base):
    __tablename__ = 'tweetmeta'
    id = Column(Integer, primary_key=True)
    TwitterId = Column(BigInteger)
    TweetTimeStamp = Column(DateTime)
    TweetHashTag = Column(String)
    crawlerLastExecutionTime = Column(DateTime)

    def __init__(self, TwitterId, TweetTimeStamp, TweetHashTag, crawlerLastExecutionTime):
        self.TwitterId = TwitterId
        self.TweetTimeStamp = TweetTimeStamp
        self.TweetHashTag = TweetHashTag
        self.crawlerLastExecutionTime = crawlerLastExecutionTime

    def __repr__(self):
        return "<TweetMeta(id='{}', TwitterId={}, TweetTimeStamp={}, TweetHashTag='{}', crawlerLastExecutionTime={})>". \
            format(self.id, self.TwitterId, self.TweetTimeStamp, self.TweetTimeStamp, self.TweetHashTag,
                   self.crawlerLastExecutionTime)
