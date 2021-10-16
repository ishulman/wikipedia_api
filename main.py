import requests
from requests.models import parse_url
import datadog
from datadog import initialize, statsd

from datetime import date, timedelta

#today = date.today().strftime('%Y%m%d')
yesterday = (date.today() - timedelta(days=2)).strftime('%Y%m%d')
print(yesterday)

languages = ["en", "de", "es", "fr"]
access = ["desktop", "mobile-app", "mobile-web"]

def get_wiki_stats_l(lang):
    api_url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/" + lang + ".wikipedia.org/all-access/all-agents/Datadog/daily/" + str(yesterday) + "/" + str(yesterday)
    hdr = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(api_url, headers=hdr)
    data = response.json()
    return data['items'][0]['views']

def get_wiki_stats_a(access):
    api_url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/"+ access + "/all-agents/Datadog/daily/" + str(yesterday) + "/" + str(yesterday)
    hdr = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(api_url, headers=hdr)
    data = response.json()
    return data['items'][0]['views']

for l in languages:
    views_yesterday = get_wiki_stats_l(l)
    print(views_yesterday)
    statsd.histogram('wiki.views_yesterday', views_yesterday, tags=[l])

for a in access:
    views_yesterday_access = get_wiki_stats_a(a)
    print(views_yesterday_access)
    statsd.histogram('wiki.views_yesterday_access', views_yesterday_access, tags=[a])


