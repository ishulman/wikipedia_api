import requests
import datadog
from datadog import initialize, statsd

api_url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia.org/all-access/all-agents/Datadog/monthly/20200101/20210101"
hdr = {'User-Agent': 'Mozilla/5.0'}
response = requests.get(api_url, headers=hdr)
data = response.json()

print(data['items'][0]['views'])

last_month_views = data['items'][0]['views']

statsd.histogram('wiki.dd.monthly_views', last_month_views, tags=["monthly_views"])
