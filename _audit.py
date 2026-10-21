#!/usr/bin/env python3
"""Additional checks, independent of the unchanged strict shared validator."""
import collections, hashlib, json, pathlib, re, urllib.parse, xml.etree.ElementTree as ET
W=pathlib.Path(__file__).resolve().parent
m=json.loads((W/'meta.json').read_text()); O=pathlib.Path(m['repo_dir'])
units=[json.loads(s) for s in (W/'units.jsonl').read_text().splitlines() if s]
comments={}; counts=collections.Counter()
for p in sorted((W/'commentary').glob('*.md')):
    for block in re.split(r'^=== ',p.read_text(),flags=re.M)[1:]:
        uid,body=block.split('\n',1); counts[uid]+=1; comments[uid]=body.strip()
raw=ET.parse(W/'sources/aktg.xml').getroot()
expected=[n.findtext('metadaten/enbez') for n in raw.findall('norm') if re.search(r'§\s*\d',n.findtext('metadaten/enbez','')) or n.findtext('metadaten/enbez') == 'Eingangsformel']
parsed=[u['label'] for u in units]
lookup={n.findtext('metadaten/enbez'):n for n in raw.findall('norm') if n.find('metadaten/enbez') is not None}
def compact(s): return re.sub(r'\s+','',s)
text_mismatches=[]; original_chars=0
for u in units:
    body=lookup[u['label']].find('textdaten/text/Content')
    original=''.join(body.itertext()) if body is not None else ''
    original_chars+=len(compact(original))
    if compact(original)!=compact(u['text']): text_mismatches.append(u['id'])
html=(W/'sources/index.html').read_text(encoding='iso-8859-1')
numbered_links=[x for x in re.findall(r'href="([^"#]+\.html)"',html) if re.search(r'(?:__\d|___\d)',x)]
index_ids=['p'+'-'.join(re.findall(r'\d+[a-z]?',x.rsplit('/',1)[-1].split('.')[0])) for x in numbered_links]
raw_agreement={'xml_text_units':len(units),'xml_original_nonwhitespace_chars':original_chars,'text_mismatches':text_mismatches,'verbatim_raw_xml_text_agreement':1.0 if not text_mismatches else None,'index_numbered_links':len(numbered_links),'index_missing_ids':sorted(set(index_ids)-set(u['id'] for u in units)),'index_unexpected_ids':sorted(set(u['id'] for u in units if u['id'] != 'Eingangsformel')-set(index_ids)),'range_links':[x for x in numbered_links if '___' in x],'method':'Independent XML itertext concatenation, removal of whitespace only; compared by official label; independent HTML link enumeration. No use of canonical text.'}
(W/'raw-text-agreement.json').write_text(json.dumps(raw_agreement,ensure_ascii=False,indent=2)+'\n')
sent=collections.defaultdict(set)
for uid,body in comments.items():
    for s in re.split(r'(?<=[.!?])\s+',body):
        if len(s)>100: sent[s].add(uid)
repeats=[{'sentence':s,'ids':sorted(ids)} for s,ids in sent.items() if len(ids)>1]
links=[]
for p in O.rglob('*.md'):
    if 'sources' in p.relative_to(O).parts or p.name.startswith('KORE'):continue
    for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('https://','http://','#','mailto:')):continue
        local=urllib.parse.unquote(target.split('#')[0])
        if local and not (p.parent/local).exists(): links.append({'file':str(p.relative_to(O)),'target':target})
manifest=[]
for parent in [W/'sources',W/'authorities',W/'cases']:
    for p in sorted(parent.rglob('*')):
        if p.is_file():manifest.append({'path':str(p.relative_to(W)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(W/'source-manifest.json').write_text(json.dumps({'generated_from':'saved source files','files':manifest},ensure_ascii=False,indent=2)+'\n')
r={'expected_count':len(expected),'parsed_count':len(parsed),'missing_official_identifiers':sorted(set(expected)-set(parsed)),'extra_identifiers':sorted(set(parsed)-set(expected)),'duplicate_statutory_ids':[x for x,c in collections.Counter(u['id'] for u in units).items() if c>1],'completed_commentary_units':len(comments),'missing_commentary_units':[u['id'] for u in units if u['id'] not in comments],'duplicate_commentary_blocks':[x for x,c in counts.items() if c>1],'commentary_chars':sum(len(c) for c in comments.values()),'ordinary_below_700':[{'id':u['id'],'chars':len(comments[u['id']])} for u in units if u['id'] in comments and len(u['text'])>=160 and len(comments[u['id']])<700],'repeated_long_sentences':repeats,'broken_local_links':links,'source_xml_sha256':hashlib.sha256((W/'sources/aktg.xml').read_bytes()).hexdigest(),'full_manuscript_complete':len(comments)==len(units)}
(W/'audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:r[k] for k in ['expected_count','parsed_count','completed_commentary_units','commentary_chars','ordinary_below_700','repeated_long_sentences','broken_local_links','full_manuscript_complete']},ensure_ascii=False))
