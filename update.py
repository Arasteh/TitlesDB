import requests
import itertools
import time
import json

queryResult = requests.post('https://query.wikidata.org/bigdata/namespace/wdq/sparql', '''
SELECT DISTINCT ?qid
WHERE {
  ?qid wdt:P495 wd:Q794. # Iran (Q794) is country of origin (P495)
  ?qid wdt:P3383 ?x.     # Item has a film poster (P3383)
}
''', headers={'Content-Type':'application/sparql-query', 'Accept': 'application/json'})

def wikidata_items(ids):
    for batch in itertools.batched(ids, 50):
        yield from requests.post(
            'https://www.wikidata.org/w/api.php',
            {'action': 'wbgetentities', 'format': 'json', 'ids': '|'.join(batch)}
        ).json()['entities'].values()
        print('fetched 50 items, sleep for 2s')
        time.sleep(2)
    print('finished')

ids = [x['qid']['value'].split('entity/')[1] for x in queryResult.json()['results']['bindings']]

result = []
for item in wikidata_items(ids):
    result.append({
        'id': item['id'],
        'sitelinks': {site: link['title'] for site, link in item['sitelinks'].items() if site == 'fawiki' or site == 'enwiki'},
        'labels': {lang: label['value'] for lang, label in item['labels'].items() if lang == 'fa' or lang == 'en'},
        'date': [x['mainsnak']['datavalue']['value']['time'] for x in item['claims'].get('P577', [])],
        'imdb': [x['mainsnak']['datavalue']['value'] for x in item['claims'].get('P345', [])],
        'poster': [{
            'image': poster['mainsnak']['datavalue']['value'],
            'designer': [x['datavalue']['value']['id'] for x in poster.get('qualifiers', {}).get('P170', {})],
        } for poster in item['claims'].get('P3383', [])],
    })

designers = {
    item['id']: {lang: label['value'] for lang, label in item['labels'].items() if lang == 'fa' or lang == 'en'}
    for item in wikidata_items(
        ({designer
          for item in result
          for poster in item['poster']
          for designer in poster['designer']})
    )
}

posters = [
    {**item,
     'poster': poster['image'],
     'designer': {designer: designers[designer] for designer in poster['designer']}}
    for item in result
    for poster in item['poster']
]

print(json.dumps(posters, indent=2, ensure_ascii=False))
