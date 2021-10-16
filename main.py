import requests
import datadog
from datadog import initialize, statsd

from datetime import date

today = date.today().strftime('%Y%m%d')

languages = ["en", "de", "es", "fr"]

def get_wiki_stats(lang):
    api_url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/" + lang + ".wikipedia.org/all-access/all-agents/Datadog/daily/20200101/" + str(today)
    hdr = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(api_url, headers=hdr)
    data = response.json()
    return data['items'][0]['views']


for l in languages:
    views_today = get_wiki_stats(l)
    statsd.histogram('wiki.dd.views_today', views_today, tags=[l])


#views_today = data['items'][0]['views']
#statsd.histogram('wiki.dd.views_today', views_today, tags=["monthly_views"])
