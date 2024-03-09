# Postgres setup

change `DATABASE_URI` in `crud.py` file and `config.py` file

Run `python crud.py`, which generates `**tweetmeta**` tabel in database

crud.py do postgres table generaion.

DATABASE_URI = "postgres+psycopg2://postgres:password@localhost:5432/tweetdb"
password = your local postgres password
5432 is port no. of postgres 


***

If in future `models.py` changes,
Run  `alembic revision --autogenerate -m "###YOUR COMMENT###"`
Run  `alembic upgrade head`
Which will do required table changes in database.


# sentiment part

after crawling part you should run test.py and get sentiments of each tweet in mongodb.

Please use avi-CNN_best_weights.02-0.8329.hdf5 from Google drive for local run.


# server setup

test.sh cron for "don't remember || i will update it later"

test2.sh cron for every 3 hour crawling tweetscraper and scheduler.py
