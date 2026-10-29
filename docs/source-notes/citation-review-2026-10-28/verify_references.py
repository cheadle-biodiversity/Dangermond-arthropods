"""Read-only bibliographic verification against DOI registration metadata."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json,re,time
import requests

BASE=Path(__file__).resolve().parent
data=json.loads((BASE/'input_references.json').read_text())
refs=data['references']

def verify(item):
    text=item['text'].strip()
    match=re.search(r'10\.\d{4,9}/[^\s]+',text)
    doi=match.group().rstrip('.,;') if match else ''
    result=dict(original=text,doi=doi,original_index=item['i'])
    if doi:
        for service,url in [('crossref','https://api.crossref.org/works/'+doi),('datacite','https://api.datacite.org/dois/'+doi)]:
            try:
                r=requests.get(url,timeout=35,headers={'User-Agent':'DangermondCitationReview/1.0'})
                if r.status_code==200:
                    result.update(service=service,metadata=r.json(),status='verified DOI registration');break
                result[service+'_status']=r.status_code
            except Exception as e:result[service+'_error']=str(e)
        else:result['status']='DOI not verified'
    else:
        result['status']='manual primary-source review needed'
    return result

with ThreadPoolExecutor(max_workers=5) as ex:out=list(ex.map(verify,refs))
(BASE/'doi_verification.json').write_text(json.dumps(out,indent=2)+'\n')
for x in out:
    m=x.get('metadata',{}).get('message',{})
    if m:
        print(json.dumps(dict(index=x['original_index'],doi=x['doi'],title=m.get('title'),author=m.get('author'),year=m.get('published',m.get('issued')),journal=m.get('container-title'),volume=m.get('volume'),issue=m.get('issue'),pages=m.get('page'),article=m.get('article-number'))))
    elif x['status']=='DOI not verified':print('UNVERIFIED',x['doi'])
