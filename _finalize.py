import pathlib,json,hashlib,sys,shutil,datetime,collections
W=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,'/Volumes/LaCie/open-commentary/_tools')
from build_repo import load_units,load_commentary
O=pathlib.Path(json.loads((W/'meta.json').read_text())['repo_dir'])
J=lambda p:json.loads((W/p).read_text())
def save(p,d): (W/p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
u=load_units(str(W));c=load_commentary(str(W));b=J('batch-review-ledger.json')['batches']; ids=[];findings=[]
for k,v in b.items():
 r=v['review'];assert r['complete'] and not r['unresolved_blockers'];ids+=r['reviewed_ids']
 for f in r['findings']:
  if f.get('commentary_sha256'): assert hashlib.sha256(c[f['id']].encode()).hexdigest()==f['commentary_sha256'],f['id']
  findings.append(dict(f,batch_ledger_key=k))
assert len(ids)==len(set(ids))==len(u)==393 and set(ids)=={x['id'] for x in u}
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
limitations=['Selektive Rechtsprechungsrecherche; keine erschöpfende Folgeentscheidungsprüfung.','Amtliche Konsolidierung und zuletzt ausgewiesene Novelle einschließlich Inkrafttreten geprüft; keine lückenlose Sichtung sämtlicher späteren Gesetzblätter.','Abschlussmontage auf Grundlage der dokumentierten Einzelprüfungen; keine zusätzliche unabhängige Durchsicht durch diesen Finalisierungslauf und keine externe anwaltliche Freigabe.','Technische Prüfungen belegen keine juristische Fehlerfreiheit.']
save('review-result.json',dict(complete=True,task='finalize_ledger_aggregation',units_reviewed=393,reviewed_ids=ids,unresolved_blockers=[],findings=findings,limitations=limitations,basis='batch-review-ledger.json',new_units_reviewed_in_finalization=0,assembled_at=now))
old=(W/'REVIEW.md').read_text();
if not (W/'REVIEW-history.md').exists(): (W/'REVIEW-history.md').write_text(old)
rows=[]
for n,v in enumerate(b.values(),1):
 r=v['review']; rows.append(f"| {n:02d} | {r['reviewed_ids'][0]} – {r['reviewed_ids'][-1]} | {len(r['reviewed_ids'])} | [Einzelbefunde](review-result-batch-{n:03d}.json) |")
(W/'REVIEW.md').write_text('''# Prüfbericht und Abschlussmontage

Stand: 21. Oktober 2026. Der Abschlusslauf führt die 20 dokumentierten Prüfbatches zusammen. Nach dem [Ledger](batch-review-ledger.json) wurden alle 393 Einheiten einschließlich Eingangsformel in begrenzten zweiten Durchsichten geprüft. Keine Einheit fehlt oder ist doppelt zugeordnet; kein Batch meldet einen ungelösten Blocker. Alle in den Einzelbefunden gespeicherten Kommentar-Hashes stimmen mit dem montierten Manuskript überein. Die ursprüngliche Durchsicht der ersten 20 Einheiten bleibt in review-result-batch-001.json erhalten.

Dieser Lauf hat die bereits geprüften Erläuterungen nicht erneut verfasst oder selbst als unabhängig geprüft zertifiziert. [Aggregierte Einzelbefunde](review-result.json) und [historischer Prüfverlauf](REVIEW-history.md) dokumentieren Herkunft und Grenzen. Aussagen über fehlende Kommentare im historischen Verlauf beschreiben damalige Zwischenstände.

| Batch | Kennungen | Anzahl | Nachweis |
| --- | --- | ---: | --- |
'''+ '\n'.join(rows)+'''

Die reproduzierbare Extraktion umfasst 393 amtliche Einheiten: Eingangsformel und 392 nummerierte Datensätze, einschließlich ausdrücklich leerer und zusammengefasster Wegfallstellen. Keine operative Anlage ist im amtlichen XML ausgewiesen. Das weggefallene Vierte Buch wird als Gliederung erhalten; nicht einzeln enthaltene §§ 339–393 werden nicht erfunden. [Vollständigkeit](completeness-report.json), [direkter XML-Textvergleich](raw-text-agreement.json), [technischer Audit](audit.json).

Maßgeblich ist der Autorentag 19. Oktober 2026. Die Quellen-Preflights unterscheiden die seit 10. Februar 2026 wirksame Centöffnung, die erst 2030 wirksamen Teile des Artikels 23 und den erst am 4. Dezember 2026 wirksamen Artikel 24. [Preflight](preflight-result.json), [Abrufe und Hashes](sources/verification.json). Die mehrfach neu abgerufene AktG-XML stimmt mit der gesicherten Intake-XML überein.

Die Fallkarten und Suchprotokolle enthalten selektiv geprüfte amtliche Volltexte mit Aussagegrenzen. Die Montage übernimmt deren Prüfnachweise; sie behauptet keine vollständige Rechtsprechungsabdeckung. Externe Verweisungsnormen sind nur im dokumentierten Umfang geprüft. Eine lückenlose Kontrolle sämtlicher späterer Bundesgesetzblätter und eine externe anwaltliche Freigabe liegen nicht vor. Wortlaut-, Längen-, Verknüpfungs- und Wiederholungsprüfungen ersetzen keine juristische Bewertung.

Das Ergebnis ist ein vollständig montierter Arbeitsentwurf mit dokumentierten Batchprüfungen. Keine Veröffentlichung oder externe Einreichung. Die aktuellen technischen Ergebnisse stehen in [validation.json](validation.json) und [finalization-result.json](finalization-result.json).
''')
s=(W/'README.md').read_text();start=s.index('**Arbeitsentwurf');end=s.index('\n\nGegenstand',start)
s=s[:start]+ '**Vollständig montierter Arbeitsentwurf vom 21. Oktober 2026.** Alle 393 amtlichen Einheiten (Eingangsformel und 392 nummerierte Datensätze) sind in 20 Kapiteln kommentiert. Die 20 im Ledger dokumentierten zweiten Durchsichten decken sämtliche Einheiten ab. Der Abschlusslauf bündelt diese Nachweise und führt die technische Gesamtprüfung aus; er ist keine zusätzliche unabhängige juristische Begutachtung.'+s[end:]
s=s.replace('Die [Vollständigkeitsprüfung](completeness-report.json) bezieht sich auf die Extraktion, nicht auf die Fertigstellung des Kommentars.','Die [Vollständigkeitsprüfung](completeness-report.json) dokumentiert die Extraktion; der Kommentierungs- und Prüfstand ist gesondert nachgewiesen.')
pos=s.index('Der Entwurf wird ohne Gewähr');s=s[:pos]+'''Der Entwurf wird ohne Gewähr bereitgestellt und ersetzt keine Prüfung des Einzelfalls. [Prüfbericht](REVIEW.md), [aggregierte Einzelbefunde](review-result.json) und [Ledger](batch-review-ledger.json) weisen die begrenzten zweiten Durchsichten nach. Eine externe fachliche Freigabe liegt nicht vor. Veröffentlichung, Push oder externe Einreichung erfolgten nicht. Die technischen Ergebnisse sind in [validation.json](validation.json) und [finalization-result.json](finalization-result.json) dokumentiert.
''';(W/'README.md').write_text(s)
p=W/'00-einleitung.md';s=p.read_text();s=s.replace('Die Fortsetzung über § 206 hinaus ist noch offen. Die vollständige Quellenextraktion ist deshalb nicht mit einem vollständigen Manuskript zu verwechseln.','Der vollständige Band umfasst außerdem Kapitalherabsetzung, Beschlussmängel, Auflösung, KGaA, Unternehmensverträge, Konzernverantwortung, Eingliederung, Ausschluss sowie Sonder-, Straf- und Schlussvorschriften.').replace('auch soweit das spätere Kommentarkapitel noch fehlt','mit den jeweiligen Kommentarkapiteln').replace('Die Rechtsprechungsarbeit beschränkt sich bisher auf drei dokumentierte BGH-Entscheidungen und die im Suchprotokoll angegebenen Rechercheschritte.','Die Rechtsprechungsarbeit umfasst die in den Fallkarten und Suchprotokollen dokumentierte selektive Auswahl amtlicher Volltexte.').replace('Der Status bleibt bis zur Fertigstellung aller 393 Einheiten und der Gesamtprüfung offen.','Alle 393 Einheiten sind kommentiert und nach dem Batch-Ledger geprüft; der montierte Text bleibt ein Arbeitsentwurf ohne externe fachliche Freigabe.');p.write_text(s)
# Copy only manuscript evidence, preserving all other existing output files.
for directory in ['sources','authorities','cases']:
 if (W/directory).exists():shutil.copytree(W/directory,O/directory,dirs_exist_ok=True)
for p in W.iterdir():
 if p.is_file() and (p.suffix in ['.json','.md']) and not p.name.startswith(('author-result','batch-progress','preflight-cache','production-','review-assignment')):
  shutil.copy2(p,O/p.name)
shutil.copy2('/Volumes/LaCie/open-commentary/_tools/LICENSE',O/'LICENSE')
save('finalization-result.json',dict(task='finalize',assembled_at=now,ledger_batches=20,ledger_reviewed_units=393,commentary_hash_mismatches=[],new_units_authored=0,new_units_reviewed=0,limitations=limitations,complete=False))
