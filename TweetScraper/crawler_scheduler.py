import psycopg2
import subprocess
import random, time

try:
    conn = psycopg2.connect(host="localhost", database="tweetdb", user="postgres", password="postgres")
except:
    print("DB Connection Failed")

cursor = conn.cursor()

cursor.execute("SELECT tweet_hashtag, id FROM myapi_tweetmeta")
values = cursor.fetchall()



for every_value in values:
    print(every_value[0], str(every_value[1]))
    # subprocess.check_call(['./run_crawler.sh', every_value[0], str(every_value[1])])
    # print("Crawler running on " + every_value[0])
    # timeDelay = random.randrange(1, 10)
    # print("Time delay " + str(timeDelay))
    # time.sleep(timeDelay)


