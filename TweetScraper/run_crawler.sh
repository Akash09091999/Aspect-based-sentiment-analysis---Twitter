#!/bin/bash
scrapy crawl TweetScraper -a query=$1 -a local_id=$2