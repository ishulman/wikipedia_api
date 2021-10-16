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

def get_wiki_stats_a(lang, access):
    api_url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/" + lang + access + "/all-agents/Datadog/daily/" + str(yesterday) + "/" + str(yesterday)
    hdr = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(api_url, headers=hdr)
    data = response.json()
    return data['items'][0]['views']

for l in languages:
    views_yesterday = get_wiki_stats_l(l)
    views_yesterday_desktop = get_wiki_stats_a(l, "desktop")
    views_yesterday_mobile_app = get_wiki_stats_a(l, "mobile-app")
    views_yesterday_mobile_web = get_wiki_stats_a(l, "mobile-web")

    statsd.histogram('wiki.views_yesterday', views_yesterday, tags=[l])
    statsd.histogram('wiki.views_yesterday_desktop', views_yesterday_desktop, tags=[l])
    statsd.histogram('wiki.views_yesterday_mobile_app', views_yesterday_mobile_app, tags=[l])
    statsd.histogram('wiki.views_yesterdayy_mobile_web', views_yesterday_mobile_web, tags=[l])


# for a in access:
#     views_yesterday_access = get_wiki_stats_a(a)
#     print(views_yesterday_access)
#     statsd.histogram('wiki.views_yesterday_access', views_yesterday_access, tags=[l])


