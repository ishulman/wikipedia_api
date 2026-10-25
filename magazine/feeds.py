import requests, re, sys
import xml.etree.ElementTree as ET
UA={'User-Agent':'Mozilla/5.0 (LongAfternoon reader)'}
NS={'media':'http://search.yahoo.com/mrss/','dc':'http://purl.org/dc/elements/1.1/','content':'http://purl.org/rss/1.0/modules/content/'}
def fetch(url):
    r=requests.get(url,headers=UA,timeout=30); root=ET.fromstring(r.content); out=[]
    for it in root.iter('item'):
        g=lambda t:(it.findtext(t) or '').strip()
        img=None
        for m in it.findall('media:content',NS)+it.findall('media:thumbnail',NS)+it.findall('enclosure'):
            u=m.get('url'); 
            if u: img=u; break
        if not img:
            c=it.findtext('content:encoded',namespaces=NS) or ''
            m=re.search(r'<img[^>]+src="([^"]+)"',c); img=m.group(1) if m else None
        out.append(dict(title=g('title'),link=g('link'),date=g('pubDate'),by=(it.findtext('dc:creator',namespaces=NS) or '').strip(),desc=re.sub(r'<[^>]+>','',g('description')).strip(),img=img))
    return out
if __name__=='__main__':
    for u in sys.argv[1:]:
        items=fetch(u); print('==',u,len(items))
        for i in items[:12]: print('-',i['title'][:80],'|',i['by'][:25],'|',i['date'][:16],'| img' if i['img'] else '| -')
