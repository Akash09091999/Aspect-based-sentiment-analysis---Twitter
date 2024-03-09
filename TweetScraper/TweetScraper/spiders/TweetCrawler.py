import psycopg2
import pytz
from scrapy.exceptions import CloseSpider
from scrapy.spiders import CrawlSpider, Rule
from scrapy.selector import Selector
from scrapy import http
from scrapy.shell import inspect_response  # for debugging
import re
import json
import time
import logging
from lxml import html

try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+

from datetime import datetime

from TweetScraper.items import Tweet, User

# from models import TweetMeta
# from crud import Session

from bs4 import BeautifulSoup

import sqlite3

try:
    conn = psycopg2.connect(host="localhost", database="tweetdb", user="postgres", password="postgres")
except:
    raise CloseSpider('No metadata database connected')

# cursor_obj = connection.cursor()
# temp_data = cursor_obj.execute("SELECT * FROM tweets")
# print('tempData')
# print(temp_data.fetchone())

from nltk.tokenize import WordPunctTokenizer
tok = WordPunctTokenizer()

pat1 = r'@[A-Za-z0-9_]+'
pat2 = r'https?://[^ ]+'
# pat2 = r'(?:https?:\/\/)?(?:www\.)?[a-z-]+\.(?:com|org)(?:\.[a-z]{2,3})?'
combined_pat = r'|'.join((pat1, pat2))
www_pat = r'www.[^ ]+'
negations_dic = {"isn't":"is not", "aren't":"are not", "wasn't":"was not", "weren't":"were not",
                "haven't":"have not","hasn't":"has not","hadn't":"had not","won't":"will not",
                "wouldn't":"would not", "don't":"do not", "doesn't":"does not","didn't":"did not",
                "can't":"can not","couldn't":"could not","shouldn't":"should not","mightn't":"might not",
                "mustn't":"must not"}
neg_pattern = re.compile(r'\b(' + '|'.join(negations_dic.keys()) + r')\b')


def tweet_cleaner_updated(text):
    soup = BeautifulSoup(text, 'lxml')
    souped = soup.get_text()
    try:
        bom_removed = souped.decode("utf-8-sig").replace(u"\ufffd", "?")
    except:
        bom_removed = souped
    stripped = re.sub(combined_pat, '', bom_removed)
    stripped = re.sub(www_pat, '', stripped)
    lower_case = stripped.lower()
    neg_handled = neg_pattern.sub(lambda x: negations_dic[x.group()], lower_case)
    letters_only = re.sub("[^a-zA-Z]", " ", neg_handled)
    # During the letters_only process two lines above, it has created unnecessay white spaces,
    # I will tokenize and join together to remove unneccessary white spaces
    words = [x for x  in tok.tokenize(letters_only) if len(x) > 1]
    return (" ".join(words)).strip()


logger = logging.getLogger(__name__)


class TweetScraper(CrawlSpider):
    name = 'TweetScraper'
    allowed_domains = ['twitter.com']

    def __init__(self, query='', local_id= '', last_tweet_time= '', last_tweet_id= '', lang='', crawl_user=False, top_tweet=False):

        self.close_spider = True
        self.query = query
        self.local_id = int(local_id)
        self.fetch_upto_id = last_tweet_id
        self.url = "https://twitter.com/search/"

        if not top_tweet:
            self.url = self.url + "&f=tweets"

        self.url = self.url + "&q=%s&src=typed&max_position=%s"

        self.crawl_user = crawl_user
        self.save_first = True  # Flag to save first tweet

        self.tweet_count = 0

        self.curr = conn.cursor()
        dt = datetime.now()
        update_crawler_time_query = "UPDATE myapi_tweetmeta SET crawler_lastexecutiontime = %s WHERE id = %s"
        self.curr.execute(update_crawler_time_query, (dt, self.local_id))
        conn.commit()
        self.curr.execute("SELECT twitter_id, tweet_timestamp, if_first FROM myapi_tweetmeta WHERE id= %s", (self.local_id, ))
        data = self.curr.fetchone()
        print(data)
        self.fetch_upto_id = data[0]
        self.last_date_obj = data[1]
        self.fetch_upto_date = data[1]
        self.if_first = data[2]
        if self.if_first == 1:
            self.curr.execute("UPDATE myapi_tweetmeta SET if_first = %s WHERE id = %s", (0, self.local_id))

    def start_requests(self):
        url = self.url % (quote(self.query), '')
        
        print("Url",url)
        print("Hello scrapy!")
        yield http.Request(url, callback=self.parse_page)

    def parse_page(self, response):
        # inspect_response(response, self)
        # handle current page
        print("================================================")
        print(response.body)
        data = json.loads(response.body.decode("utf-8"))

        # close spider if there is tweet
        if self.if_first and self.tweet_count > 100 :
            self.curr.execute("UPDATE myapi_tweetmeta SET if_first = %s where id= %s", (0, self.local_id))
            raise CloseSpider('It was first time crawl... wooooopie new hashtag')

        for item in self.parse_tweets_block(data['items_html']):
            yield item

        # get next page
        min_position = data['min_position']
        min_position = min_position.replace("+", "%2B")
        url = self.url % (quote(self.query), min_position)
        print("Page parsed")
        print(self.tweet_count)
        yield http.Request(url, callback=self.parse_page)

    def parse_tweets_block(self, html_page):
        page = Selector(text=html_page)

        ### for text only tweets
        items = page.xpath('//li[@data-item-type="tweet"]/div')
        for item in self.parse_tweet_item(items):
            yield item

    def parse_tweet_item(self, items):
        for item in items:
            try:
                tweet = Tweet()
                self.tweet_count += 1

                tweet['usernameTweet'] = \
                    item.xpath('.//span[@class="username u-dir u-textTruncate"]/b/text()').extract()[0]

                ID = item.xpath('.//@data-tweet-id').extract()
                if not ID:
                    continue
                tweet['ID'] = ID[0]

                ### get text content
                p_txt = item.xpath('.//div[@class="js-tweet-text-container"]/p').extract()
                p_txt = " ".join(p_txt)
                p = html.fromstring(p_txt)
                a_links = p.xpath("//p/a")
                for a in a_links:
                    if 'twitter-atreply' in a.attrib['class']:
                        # for getting @xyz mentions
                        txt = a.attrib['href'].split("/")[1]
                        for child in list(a):
                            a.remove(child)
                        a.text = txt
                    elif 'twitter-hashtag' in a.attrib['class']:
                        # for getting #xyz hashtag
                        txt = a.attrib['href'].split("?")[0].split("/")[2]
                        for child in list(a):
                            a.remove(child)
                        a.text = txt
                    elif 'twitter-timeline-link u-hidden' in a.attrib['class']:
                        # For removing pic.twitter.... link that sometimes comes up in the bottom of a tweet
                        for child in list(a):
                            a.remove(child)
                        a.text = ""
                    elif 'twitter-timeline-link' in a.attrib['class'] and 'data-expanded-url' in a.attrib:
                        # for getting embedding links of type http[s]://xyz.com
                        txt = a.attrib['data-expanded-url']
                        for child in list(a):
                            #print(a.child)
                            a.remove(child)
                        a.text = txt
                text = p.xpath("//p//text()")
                tweet['text'] = ' '.join(text)
                if tweet['text'] == '':
                    # If there is not text, we ignore the tweet
                    continue
                
                tweet['text'] = tweet_cleaner_updated(tweet['text'])
                

                ### local id
                tweet['local_ID'] = self.local_id

                ### get meta data
                tweet['url'] = item.xpath('.//@data-permalink-path').extract()[0]

                nbr_retweet = item.css('span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount').xpath(
                    '@data-tweet-stat-count').extract()
                if nbr_retweet:
                    tweet['nbr_retweet'] = int(nbr_retweet[0])
                else:
                    tweet['nbr_retweet'] = 0

                nbr_favorite = item.css('span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount').xpath(
                    '@data-tweet-stat-count').extract()
                if nbr_favorite:
                    tweet['nbr_favorite'] = int(nbr_favorite[0])
                else:
                    tweet['nbr_favorite'] = 0

                nbr_reply = item.css('span.ProfileTweet-action--reply > span.ProfileTweet-actionCount').xpath(
                    '@data-tweet-stat-count').extract()
                if nbr_reply:
                    tweet['nbr_reply'] = int(nbr_reply[0])
                else:
                    tweet['nbr_reply'] = 0

                tweet['datetime'] = datetime.fromtimestamp(int(
                    item.xpath('.//div[@class="stream-item-header"]/small[@class="time"]/a/span/@data-time').extract()[
                        0])).strftime('%Y-%m-%d %H:%M:%S')

                
                
                curr_date_obj = datetime.strptime(tweet['datetime'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=pytz.timezone("Asia/Calcutta"))
                tweet['date'] = datetime.strftime(curr_date_obj, '%Y-%m-%d')
                if self.save_first:
                    print(tweet['datetime'])
                    print(tweet['ID'])
                    self.save_first = False
                    if curr_date_obj > self.last_date_obj:
                        self.last_date_obj = curr_date_obj
                        self.curr.execute("UPDATE myapi_tweetmeta SET tweet_timestamp = %s , twitter_id = %s WHERE  id = %s", (curr_date_obj, tweet['ID'], self.local_id))
                        conn.commit()

                if (curr_date_obj <= self.fetch_upto_date) and (int(tweet['ID']) <= int(self.fetch_upto_id)):
                    self.shut_spider = True
                    return

                ### get photo
                has_cards = item.xpath('.//@data-card-type').extract()
                if has_cards and has_cards[0] == 'photo':
                    tweet['has_image'] = True
                    tweet['images'] = item.xpath('.//*/div/@data-image-url').extract()
                elif has_cards:
                    logger.debug('Not handle "data-card-type":\n%s' % item.xpath('.').extract()[0])

                ### get animated_gif
                has_cards = item.xpath('.//@data-card2-type').extract()
                if has_cards:
                    if has_cards[0] == 'animated_gif':
                        tweet['has_video'] = True
                        tweet['videos'] = item.xpath('.//*/source/@video-src').extract()
                    elif has_cards[0] == 'player':
                        tweet['has_media'] = True
                        tweet['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == 'summary_large_image':
                        tweet['has_media'] = True
                        tweet['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == 'amplify':
                        tweet['has_media'] = True
                        tweet['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == 'summary':
                        tweet['has_media'] = True
                        tweet['medias'] = item.xpath('.//*/div/@data-card-url').extract()
                    elif has_cards[0] == '__entity_video':
                        pass  # TODO
                        # tweet['has_media'] = True
                        # tweet['medias'] = item.xpath('.//*/div/@data-src').extract()
                    else:  # there are many other types of card2 !!!!
                        logger.debug('Not handle "data-card2-type":\n%s' % item.xpath('.').extract()[0])

                is_reply = item.xpath('.//div[@class="ReplyingToContextBelowAuthor"]').extract()
                tweet['is_reply'] = is_reply != []

                is_retweet = item.xpath('.//span[@class="js-retweet-text"]').extract()
                tweet['is_retweet'] = is_retweet != []

                tweet['user_id'] = item.xpath('.//@data-user-id').extract()[0]
                tweet['sentiment'] = 0
                tweet['found_relevance'] = 0

                yield tweet

                if self.crawl_user:
                    ### get user info
                    user = User()
                    user['ID'] = tweet['user_id']
                    user['name'] = item.xpath('.//@data-name').extract()[0]
                    user['screen_name'] = item.xpath('.//@data-screen-name').extract()[0]
                    user['avatar'] = \
                        item.xpath('.//div[@class="content"]/div[@class="stream-item-header"]/a/img/@src').extract()[0]
                    yield user
            except:
                logger.error("Error tweet:\n%s" % item.xpath('.').extract()[0])
                # raise

    def extract_one(self, selector, xpath, default=None):
        extracted = selector.xpath(xpath).extract()
        if extracted:
            return extracted[0]
        return default
