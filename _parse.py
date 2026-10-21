#!/usr/bin/env python3
"""Reproducible GII XML extraction; no statutory wording is authored here."""
import hashlib, json, pathlib, re, xml.etree.ElementTree as ET
W = pathlib.Path(__file__).resolve().parent
RAW = W / 'sources/aktg.xml'

def render(e):
    if e is None:
        return ''
    out = e.text or ''
    for c in e:
        s = render(c)
        if c.tag in ('BR',): s = '\n'
        elif c.tag in ('P', 'DL', 'DD', 'row', 'table', 'pre'): s = '\n' + s + '\n'
        elif c.tag in ('DT',): s = '\n' + s + ' '
        elif c.tag == 'entry': s += ' '
        out += s + (c.tail or '')
    return out

def clean(s):
    s = re.sub(r'[ \t\r\f\v]+', ' ', s.replace('\xa0', ' '))
    return re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', s).strip()

CHAPTERS = [
 (22,'grundlagen','Grundlagen und Unternehmensverbindungen'),
 (53,'gruendung','Gründung und Nachgründung'),
 (75,'aktionaere','Aktionäre, Aktienregister und eigene Aktien'),
 (94,'vorstand','Vorstand und Organhaftung'),
 (117,'aufsichtsrat','Aufsichtsrat und schädlicher Einfluss'),
 (128,'hauptversammlung-vorbereitung','Hauptversammlung und Vorbereitung'),
 (149,'hauptversammlung-rechte','Mitwirkung, Sonderprüfung und Rechtsverfolgung'),
 (178,'rechnungslegung','Rechnungslegung und Gewinnverwendung'),
 (191,'satzung-kapitalerhoehung','Satzungsänderung und ordentliche Kapitalerhöhung'),
 (206,'bedingtes-genehmigtes-kapital','Bedingtes und genehmigtes Kapital'),
 (221,'gesellschaftsmittel','Kapitalerhöhung aus Gesellschaftsmitteln und Schuldverschreibungen'),
 (240,'kapitalherabsetzung','Kapitalherabsetzung und Einziehung'),
 (255,'beschlussmaengel','Beschlussmängel und zusätzliche Aktien'),
 (261,'abschlusskontrolle','Abschlussmängel und Sonderprüfung'),
 (277,'aufloesung','Auflösung, Abwicklung und Nichtigkeit'),
 (290,'kgaa','Kommanditgesellschaft auf Aktien'),
 (303,'unternehmensvertraege','Unternehmensverträge und Gläubigerschutz'),
 (318,'konzernverantwortung','Außenstehende Aktionäre und Konzernverantwortung'),
 (328,'eingliederung-ausschluss','Eingliederung, Ausschluss und wechselseitige Beteiligung'),
 (999,'sonder-schluss','Öffentliche Beteiligung, Sanktionen und Schlussvorschriften')]

def main():
    root = ET.parse(RAW).getroot()
    assert root.findtext('norm/metadaten/jurabk') == 'AktG'
    units, structures, excluded, alltext, empty = [], [], [], [], []
    for n in root.findall('norm'):
        m = n.find('metadaten'); en = clean(m.findtext('enbez', ''))
        title = clean(render(m.find('titel')))
        g = m.find('gliederungseinheit')
        if g is not None:
            code = g.findtext('gliederungskennzahl')
            structures = [(c,t) for c,t in structures if len(c) < len(code)]
            structures.append((code, clean(g.findtext('gliederungsbez','') + ' — ' + g.findtext('gliederungstitel',''))))
        text = clean(render(n.find('textdaten/text/Content')))
        notes = clean(render(n.find('textdaten/fussnoten/Content')))
        if not re.search(r'§\s*\d',en) and en != 'Eingangsformel':
            excluded.append({'doknr':n.get('doknr'),'label':en or ('Gliederung' if g is not None else 'Gesetzesmetadaten'), 'disposition':'structure' if g is not None else 'frontmatter'})
            alltext.append('\n'.join(x for x in [en,title,text,notes] if x))
            continue
        nums = re.findall(r'\d+[a-z]?',en)
        uid = 'Eingangsformel' if en == 'Eingangsformel' else 'p' + '-'.join(nums)
        first = 0 if en == 'Eingangsformel' else int(re.match(r'\d+', nums[0]).group())
        chapter = next(i+1 for i,c in enumerate(CHAPTERS) if first<=c[0])
        u = dict(id=uid,label=en,title=title,chapter=chapter,structure=[t for c,t in structures],text=text,notes=[notes] if notes else [],official_doknr=n.get('doknr'))
        if not text:
            empty.append({'id':uid,'title':title,'disposition':'Amtlich leerer Textkörper; keine ergänzte Gesetzesformulierung.'})
            u['notes'].append('Der amtliche XML-Textkörper dieser Nummer ist leer. Die Nummer und gegebenenfalls die Wegfallüberschrift werden unverändert erhalten.')
        units.append(u)
        alltext.append('\n\n'.join([en,title,text,notes]))
    canonical = W/'sources/aktg-canonical.md'
    canonical.write_text('# Aktiengesetz — maschinelle XML-Transkription\n\n'+'\n\n'.join(alltext)+'\n')
    (W/'units.jsonl').write_text(''.join(json.dumps(u,ensure_ascii=False)+'\n' for u in units))
    meta = dict(cc='de',lang='de',repo='Komentar-DE-AKTG-1965',repo_dir='/Volumes/LaCie/open-commentary/de/Komentar-DE-AKTG-1965',title='Kommentar zum Aktiengesetz',source_path=str(canonical),intro_file='00-einleitung.md',intro_desc='Geltungsstand, Methode und Benutzung',labels=dict(text='Wortlaut der Vorschrift',chapter='Kommentarkapitel',notes='Quellenhinweis'),chapters=[dict(n=i+1,slug=c[1],title=c[2]) for i,c in enumerate(CHAPTERS)])
    (W/'meta.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    # Expected sequence is independently selected from raw metadata, not units.jsonl.
    expected = [x.findtext('metadaten/enbez') for x in root.findall('norm') if re.search(r'§\s*\d',x.findtext('metadaten/enbez','')) or x.findtext('metadaten/enbez') == 'Eingangsformel']
    parsed = [u['label'] for u in units]
    report = dict(xml_sha256=hashlib.sha256(RAW.read_bytes()).hexdigest(),official_norm_records=len(root.findall('norm')),expected_official_identifiers=expected,extracted_identifiers=parsed,expected_count=len(expected),extracted_count=len(units),missing=sorted(set(expected)-set(parsed)),unexpected=sorted(set(parsed)-set(expected)),duplicates=[x for x in set(parsed) if parsed.count(x)>1],empty_slots=empty,excluded_records=excluded,annex_disposition='Keine Anlage im amtlichen XML und im amtlichen Inhaltsverzeichnis ausgewiesen. Das weggefallene Vierte Buch ist als Gliederung erhalten; die amtliche XML enthält keine Einzelnummern §§ 339–393. Diese werden nicht als geltende Vorschriften erfunden.',range_slots=[u['label'] for u in units if len(re.findall(r'\d+',u['label']))>1],limitations=['Metadatenabgleich beweist die Extraktionsvollständigkeit gegenüber dieser XML, nicht deren amtliche redaktionelle Fehlerfreiheit.'])
    report['historical_duplicates'] = [x for x in set(expected) if expected.count(x)>1]
    report['nonstructural_text_records_excluded'] = [n.get('doknr') for n in root.findall('norm') if n.find('textdaten/text/Content') is not None and n.find('metadaten/gliederungseinheit') is None and n.findtext('metadaten/enbez','') not in expected and n.findtext('metadaten/enbez','') != 'Inhaltsübersicht']
    report['ok'] = not (report['missing'] or report['unexpected'] or report['duplicates'])
    (W/'completeness-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['expected_count','extracted_count','missing','duplicates','ok']}))

if __name__ == '__main__': main()
