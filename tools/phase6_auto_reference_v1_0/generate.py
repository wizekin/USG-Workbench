"""Independent deterministic synthetic reference generator for Phase 6 Step 6.6.

The oracle constructs meaning graphs first, then realizes English/MSA Arabic text.
It never reads USG development fixtures, the candidate lexicon, parser output, or LLM labels.
"""
from __future__ import annotations
import hashlib, json, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "benchmarks/phase6-auto-reference-v1.0"
SEED = 66112026
PROFILES = {
    ("en", "en.nominal.adjective_modifier"): "adjective",
    ("en", "en.genitive.of_phrase"): "genitive",
    ("en", "en.compound.noun_noun"): "compound",
    ("en", "en.prepositional.nominal_modifier"): "prepositional",
    ("en", "en.temporal.adverbial_modifier"): "temporal",
    ("ar", "ar.nominal.adjective_modifier"): "adjective",
    ("ar", "ar.genitive.idafa"): "genitive",
    ("ar", "ar.compound.lexicalized_idafa"): "compound",
    ("ar", "ar.prepositional.nominal_modifier"): "prepositional",
    ("ar", "ar.temporal.adverbial_modifier"): "temporal",
}
# Original project lexical seeds, not copied from or annotated against any corpus.
VOCAB = {
 "en": {
  "adjectives": ["bright","quiet","silver","wooden","narrow","ancient","green","small","modern","heavy","golden","empty","fragile","curious","clean","distant","warm","sharp","gentle","blue"],
  "adjective_heads": ["lantern","library","bridge","garden","notebook","station","vessel","tower","engine","village","window","instrument","package","forest","sculpture","machine","campus","harbor","doorway","orchard"],
  "gen_heads": ["map","cover","diary","engine","roof","portrait","key","design","voice","history","plan","result","name","report","photo","memory","edge","color","title","record"],
  "gen_deps": ["Nora","Sami","Lina","Omar","Rami","Huda","Salma","Karim","Maya","Yara","Adam","Noor","Layla","Ziad","Farah","Tarek","Mona","Ali","Dina","Fadi"],
  "compound_mods": ["coffee","rain","night","school","garden","river","city","stone","data","music","book","snow","tea","water","earth","moon","sun","air","fire","sea"],
  "compound_heads": ["cup","coat","lamp","gate","path","bank","house","room","desk","bag","key","map","bus","train","bridge","tower","card","shelf","bottle","garden"],
  "prep_heads": ["museum","statue","house","school","station","bridge","monument","library","garden","tower","airport","village","harbor","theater","market","hospital","gallery","temple","stadium","castle"],
  "places": ["Cairo","Amman","Rabat","Tunis","Beirut","Doha","Muscat","Fez","Giza","Luxor","Petra","Aswan","Aqaba","Sfax","Homs","Sana","Aleppo","Jeddah","Medina","Khartoum"],
  "subjects": ["Mona","Sami","Lina","Omar","Maya","Noor","Adam","Layla","Karim","Huda","Rami","Salma","Yara","Ali","Dina","Tarek","Farah","Ziad","Fadi","Amal"],
  "verbs": ["arrived","departed","returned","spoke","resigned","traveled","visited","opened","closed","started","ended","changed","moved","reported","escaped","waited","appeared","landed","called","agreed"],
  "times": ["yesterday","today","tomorrow","recently","earlier","tonight","Monday","Friday","annually","eventually","immediately","previously","later","now","soon","already","before","afterward","presently","finally"],
  "ambiguous_pairs": [("light","house"),("paper","bag"),("green","card"),("iron","gate"),("stone","wall"),("silver","screen"),("cold","case"),("fast","track"),("dark","room"),("public","school")]
 },
 "ar": {
  "adjectives": ["الجميل","الواسع","القديم","الجديد","الصغير","الكبير","الواضح","السريع","القوي","الهادئ","النظيف","القريب","الطويل","الثقيل","الخفيف","الذكي","الأخضر","الأزرق","الأبيض","المرتفع"],
  "adjective_heads": ["البيت","الكتاب","الطريق","المصنع","المبنى","المتجر","الجسر","الميناء","المستشفى","القصر","المسجد","النهر","الجبل","المطار","المتحف","المكتب","الحاسوب","الباب","الصندوق","المركز"],
  "gen_heads": ["كتاب","باب","مفتاح","صورة","سجل","تقرير","منزل","صوت","تاريخ","خريطة","قصة","رسالة","مشروع","نتيجة","اسم","خطة","غلاف","عنوان","دفتر","قميص"],
  "gen_deps": ["نورا","سامي","ليلى","عمر","رامي","هدى","سلمى","كريم","مايا","يارا","آدم","نور","مريم","زياد","فرح","طارق","منى","علي","دينا","فادي"],
  "compound_pairs": [("كلمة","مرور"),("جهاز","تحكم"),("رأس","مال"),("مفتاح","ربط"),("مركز","بيانات"),("بطاقة","ائتمان"),("جواز","سفر"),("غرفة","نوم"),("محطة","قطار"),("مكتب","بريد"),("ماء","ورد"),("قوة","عمل"),("طائرة","شحن"),("حساب","مصرف"),("حقل","نفط"),("خط","إنتاج"),("ممر","مشاة"),("مفتاح","سيارة"),("سوق","عمل"),("قلب","مدينة")],
  "prep_heads": ["المتحف","المسجد","الجسر","القصر","السوق","المدرسة","الميناء","المطار","المسرح","المستشفى","المصنع","المركز","المكتبة","البرج","الحديقة","الملعب","الفندق","المعرض","النصب","المحطة"],
  "places": ["القاهرة","عمان","الرباط","تونس","بيروت","الدوحة","مسقط","فاس","الجيزة","الأقصر","الإسكندرية","أسوان","العقبة","صفاقس","حلب","بغداد","دمشق","جدة","المدينة","الخرطوم"],
  "subjects": ["سامي","ليلى","مريم","عمر","نور","آدم","هدى","كريم","رامي","سلمى","يارا","علي","دينا","طارق","فرح","زياد","فادي","أمل","منى","خالد"],
  "verbs": ["وصل","عاد","سافر","افتتح","أغلق","بدأ","انتهى","تحرك","ظهر","هبط","غادر","أعلن","التقى","اتصل","استقال","زار","انتقل","نجح","تغير","استيقظ"],
  "times": ["أمس","اليوم","غدا","مؤخرا","سابقا","لاحقا","الآن","قريبا","مبكرا","مساء","صباحا","أخيرا","فورا","سنويا","قبلا","حينئذ","آنذاك","دائما","حاليا","ليلا"],
  "ambiguous_pairs": [("البنك","المركزي"),("السوق","السوداء"),("الطريق","السريع"),("البيت","الأبيض"),("الكتاب","المفتوح"),("المركز","الطبي"),("المدرسة","العليا"),("الميناء","الجوي"),("المتحف","التاريخي"),("الحقل","النفطي")]
 }
}
SENSES = {
 "en": {
  "adjective": {"adjectives":("ADJ","usg.nominal.adjective"),"adjective_heads":("NOUN","usg.nominal.head")},
  "genitive": {"gen_heads":("NOUN","usg.nominal.genitive_head"),"gen_deps":("PROPN","usg.nominal.genitive_dependent")},
  "compound": {"compound_mods":("NOUN","usg.nominal.compound_modifier"),"compound_heads":("NOUN","usg.nominal.compound_head")},
  "prepositional": {"prep_heads":("NOUN","usg.nominal.head"),"places":("NOUN","usg.nominal.prepositional_component")},
  "temporal": {"subjects":("PROPN","usg.event.subject"),"verbs":("VERB","usg.event.predicate"),"times":("ADV","usg.temporal.adverb")}
 },
 "ar": {
  "adjective": {"adjective_heads":("NOUN","usg.nominal.head"),"adjectives":("ADJ","usg.nominal.adjective")},
  "genitive": {"gen_heads":("NOUN","usg.nominal.genitive_head"),"gen_deps":("NOUN","usg.nominal.genitive_dependent")},
  "compound": {},
  "prepositional": {"prep_heads":("NOUN","usg.nominal.head"),"places":("NOUN","usg.nominal.prepositional_component")},
  "temporal": {"verbs":("VERB","usg.event.predicate"),"subjects":("NOUN","usg.event.subject"),"times":("ADV","usg.temporal.adverb")}
 }
}

def tokens(text):
 out=[]; start=None
 for i,ch in enumerate(text):
  if unicodedata.category(ch)[0] in {"L","M"}:
   if start is None: start=i
  elif start is not None:
   out.append((text[start:i],start,i)); start=None
 if start is not None: out.append((text[start:],start,len(text)))
 return out

def span(text, phrase):
 ts=tokens(text); wanted=phrase.split()
 for i in range(len(ts)):
  for j in range(i,len(ts)):
   a,b=ts[i][1],ts[j][2]
   if text[a:b]==" ".join(wanted): return {"start":a,"end":b,"surface":text[a:b]}
 raise ValueError(f"cannot locate {phrase!r} in {text!r}")

def build():
 entries={}
 def add(lang,form,pos,sense):
  entries[(lang,form,pos,sense)]={"language":lang,"language_profile":"en/standard-written-1.0" if lang=="en" else "ar/modern-standard-1.0","form":form,"lemma":form,"part_of_speech":pos,"sense_id":sense,"features":{},"status":"SYNTHETIC_REFERENCE_ONLY","evidence":[]}
 cases=[]; inventory={}
 for (lang,con),kind in PROFILES.items():
  v=VOCAB[lang]
  for bucket,(pos,sense) in SENSES[lang][kind].items():
   for term in v.get(bucket,[]): add(lang,term,pos,sense)
  if lang=="en" and kind in {"adjective","genitive","prepositional"}: add(lang,"the","DET","usg.grammar.determiner")
  if lang=="en" and kind=="genitive": add(lang,"of","ADP","usg.grammar.adposition")
  if lang=="en" and kind=="prepositional": add(lang,"in","ADP","usg.nominal.prepositional_component")
  if lang=="ar" and kind=="prepositional": add(lang,"في","ADP","usg.nominal.prepositional_component")
  if lang=="ar" and kind=="compound":
   for h,m in v["compound_pairs"]:
    add(lang,h,"NOUN","usg.nominal.compound_head"); add(lang,m,"NOUN","usg.nominal.compound_modifier")
  if kind in {"adjective","compound"}:
   for h,m in v["ambiguous_pairs"]:
    if lang=="en":
     add(lang,h,"ADJ","usg.nominal.adjective"); add(lang,h,"NOUN","usg.nominal.compound_modifier")
     add(lang,m,"NOUN","usg.nominal.head"); add(lang,m,"NOUN","usg.nominal.compound_head")
    else:
     add(lang,h,"NOUN","usg.nominal.head"); add(lang,m,"ADJ","usg.nominal.adjective")
     add(lang,h,"NOUN","usg.nominal.compound_head"); add(lang,m,"NOUN","usg.nominal.compound_modifier")
  if kind=="genitive":
   if lang=="en":
    for h,d in [("portrait","Jordan")]:
     add(lang,h,"NOUN","usg.nominal.genitive_head"); add(lang,d,"PROPN","usg.nominal.genitive_dependent")
    add(lang,"of","ADP","usg.grammar.adposition"); add(lang,"the","DET","usg.grammar.determiner")
   else:
    add(lang,"أثر","NOUN","usg.nominal.genitive_head"); add(lang,"الأندلس","NOUN","usg.nominal.genitive_dependent")
  if kind=="compound" and lang=="ar":
   for term,pos,sense in [("متحف","NOUN","usg.nominal.compound_head"),("تاريخ","NOUN","usg.nominal.compound_modifier"),("متحف","NOUN","usg.nominal.genitive_head"),("تاريخ","NOUN","usg.nominal.genitive_dependent")]:
    add(lang,term,pos,sense)

  for i in range(20):
   if kind=="adjective":
    a,h=v["adjectives"][i],v["adjective_heads"][i]
    text=f"the {a} {h}" if lang=="en" else f"{h} {a}"
    roles={"MODIFIER":a,"HEAD":h} if lang=="en" else {"HEAD":h,"MODIFIER":a}
    graph={"nodes":[{"id":"n-head","type":"NOMINAL"},{"id":"n-mod","type":"PROPERTY"}],"relations":[{"type":"ATTRIBUTE","source":"n-mod","target":"n-head"}],"ambiguity":None}
    relation="ATTRIBUTE"
   elif kind=="genitive":
    h,d=v["gen_heads"][i],v["gen_deps"][i]; text=f"the {h} of {d}" if lang=="en" else f"{h} {d}"
    roles={"GENITIVE_HEAD":h,"GENITIVE_DEPENDENT":d}
    graph={"nodes":[{"id":"n-head","type":"NOMINAL"},{"id":"n-dependent","type":"NOMINAL"}],"relations":[{"type":"GENITIVE_UNSPECIFIED","source":"n-dependent","target":"n-head"}],"ambiguity":"SPECIFIC_GENITIVE_SEMANTICS_UNDERSPECIFIED"}
    relation="GENITIVE_UNSPECIFIED"
   elif kind=="compound":
    m,h=(v["compound_mods"][i],v["compound_heads"][i]) if lang=="en" else (v["compound_pairs"][i][1],v["compound_pairs"][i][0])
    text=f"{m} {h}" if lang=="en" else f"{h} {m}"
    roles={"MODIFIER":m,"HEAD":h} if lang=="en" else {"HEAD":h,"MODIFIER":m}
    graph={"nodes":[{"id":"n-head","type":"LEXICALIZED_NOMINAL_HEAD"},{"id":"n-mod","type":"LEXICALIZED_COMPONENT"}],"relations":[{"type":"LEXICALIZED_COMPOUND_COMPONENT","source":"n-mod","target":"n-head"}],"ambiguity":None}
    relation="LEXICALIZED_COMPOUND_COMPONENT"
   elif kind=="prepositional":
    h,p,c=v["prep_heads"][i],("in" if lang=="en" else "في"),v["places"][i]
    text=f"the {h} {p} {c}" if lang=="en" else f"{h} {p} {c}"
    roles={"HEAD":h,"LOCATION":f"{p} {c}"}
    graph={"nodes":[{"id":"n-head","type":"NOMINAL"},{"id":"n-location","type":"LOCATION"}],"relations":[{"type":"LOCATIVE_NOMINAL_MODIFIER","source":"n-location","target":"n-head"}],"ambiguity":None}
    relation="LOCATIVE_NOMINAL_MODIFIER"
   else:
    s,vb,t=v["subjects"][i],v["verbs"][i],v["times"][i]
    text=f"{s} {vb} {t}" if lang=="en" else f"{vb} {s} {t}"
    roles={"EVENT":f"{s} {vb}" if lang=="en" else f"{vb} {s}","TIME":t}
    graph={"nodes":[{"id":"n-event","type":"EVENT"},{"id":"n-time","type":"TIME"}],"relations":[{"type":"EVENT_TIME","source":"n-time","target":"n-event"}],"ambiguity":None}
    relation="EVENT_TIME"
   spans={r:span(text,val) for r,val in roles.items()}
   node_roles={"HEAD":"n-head","MODIFIER":"n-mod","GENITIVE_HEAD":"n-head","GENITIVE_DEPENDENT":"n-dependent","LOCATION":"n-location","EVENT":"n-event","TIME":"n-time"}
   for r,sp in spans.items():
    for node in graph["nodes"]:
     if node["id"]==node_roles[r]: node["source_span"]=sp
   cases.append({"id":f"{lang}.{kind}.positive.{i+1:02d}","language":lang,"target_construction":con,"gold_class":"POSITIVE","text":text,"reference_graph":graph,"expected_role_bindings":roles,"expected_role_spans":spans,"expected_relation_type":relation,"expected_status":"CANDIDATE","generator":{"id":"usg.phase6.automatic-reference/1.0.0","seed":SEED,"scenario":"POSITIVE"}})

  for i in range(20):
   if kind=="adjective":
    a,h=v["adjectives"][i],v["adjective_heads"][i]
    text=f"the {h} is {a}" if lang=="en" else f"{h} هو {a.removeprefix('ال')}"
   elif kind=="genitive":
    h,d=v["gen_heads"][i],v["gen_deps"][i]
    text=f"{d} found the {h}" if lang=="en" else f"{d} يملك {h}"
   elif kind=="compound":
    m,h=(v["compound_mods"][i],v["compound_heads"][i]) if lang=="en" else (v["compound_pairs"][i][1],v["compound_pairs"][i][0])
    text=f"the {h} is for {m}" if lang=="en" else f"{h} مصنوع من {m}"
   elif kind=="prepositional":
    h,c=v["prep_heads"][i],v["places"][i]
    text=f"the {h} welcomed {c}" if lang=="en" else f"{h} يضم {c}"
   else:
    s,t=v["subjects"][i],v["times"][i]
    text=f"{s} is a teacher {t}" if lang=="en" else f"{s} هو المعلم {t}"
   cases.append({"id":f"{lang}.{kind}.negative.{i+1:02d}","language":lang,"target_construction":con,"gold_class":"NEGATIVE","text":text,"reference_graph":{"nodes":[{"id":"n-source","type":"SURFACE_SEQUENCE"}],"relations":[],"ambiguity":None},"expected_role_bindings":{},"expected_role_spans":{},"expected_relation_type":None,"expected_status":"ABSTAIN","generator":{"id":"usg.phase6.automatic-reference/1.0.0","seed":SEED,"scenario":"NEGATIVE"}})

  for i in range(10):
   if kind=="adjective" or (kind=="compound" and lang=="en"):
    h,m=v["ambiguous_pairs"][i]
    text=f"{h} {m}"
    graph={"nodes":[{"id":"n-1","type":"NOMINAL_OR_PROPERTY"},{"id":"n-2","type":"NOMINAL_OR_PROPERTY"}],"relations":[],"ambiguity":"ADJECTIVE_MODIFIER_VS_COMPOUND_OR_LEXICALIZED_READING","alternative_relations":[{"construction":"ADJECTIVE_MODIFIER","interpretation":"ATTRIBUTE"},{"construction":"NOUN_COMPOUND","interpretation":"LEXICALIZED_OR_COMPOSITIONAL_NOMINAL"}]}
    expected="AMBIGUOUS"
   elif kind=="genitive":
    h,d=("portrait","Jordan") if lang=="en" else ("أثر","الأندلس")
    if i: h,d=(v["gen_heads"][(i+3)%20],v["gen_deps"][(i+7)%20])
    text=f"the {h} of {d}" if lang=="en" else f"{h} {d}"
    graph={"nodes":[{"id":"n-head","type":"NOMINAL"},{"id":"n-dependent","type":"NOMINAL"}],"relations":[{"type":"GENITIVE_UNSPECIFIED","source":"n-dependent","target":"n-head"}],"ambiguity":"GENITIVE_RELATION_NOT_UNIQUELY_SPECIFIED"}
    expected="CANDIDATE_UNSPECIFIED"
    # Ensure no genitive ambiguous pair duplicates a positive pair.
    if i and (i+3)%20==(i+7)%20: raise ValueError("bad genitive ambiguity pair")
   elif kind=="compound":
    h,m=("light","house") if lang=="en" else ("متحف","تاريخ")
    text=f"{h} {m}"
    graph={"nodes":[{"id":"n-head","type":"NOMINAL"},{"id":"n-dependent","type":"NOMINAL"}],"relations":[],"ambiguity":"COMPOSITIONAL_GENITIVE_VS_LEXICALIZED_COMPOUND","alternative_relations":[{"construction":"GENITIVE_IDAFA","interpretation":"GENITIVE_UNSPECIFIED"},{"construction":"LEXICALIZED_COMPOUND","interpretation":"LEXICALIZED_COMPOUND_COMPONENT"}]}
    expected="AMBIGUOUS"
   elif kind=="prepositional":
    h,c=v["prep_heads"][i],v["places"][i]
    if lang=="en": text=f"the {h} in {c} near {v['places'][(i+1)%20]}"
    else: text=f"{h} في {c} قرب {v['places'][(i+1)%20]}"
    graph={"nodes":[{"id":"n-head","type":"NOMINAL"},{"id":"n-pp1","type":"PREPOSITIONAL_PHRASE"},{"id":"n-pp2","type":"PREPOSITIONAL_PHRASE"}],"relations":[],"ambiguity":"PREPOSITIONAL_ATTACHMENT_NOT_UNIQUE","alternative_relations":[{"attachment":"NOMINAL_HEAD","status":"POSSIBLE"},{"attachment":"EMBEDDED_NOMINAL_OR_CLAUSE","status":"POSSIBLE"}]}
    expected="ABSTAIN"
   else:
    s,vb,t=v["subjects"][i],v["verbs"][i],v["times"][i]
    s2,vb2,t2=v["subjects"][(i+1)%20],v["verbs"][(i+1)%20],v["times"][(i+1)%20]
    text=f"{s} {vb} {t} while {s2} {vb2} {t2}" if lang=="en" else f"{vb} {s} {t} ثم {vb2} {s2} {t2}"
    graph={"nodes":[{"id":"n-event-1","type":"EVENT"},{"id":"n-event-2","type":"EVENT"},{"id":"n-time-1","type":"TIME"},{"id":"n-time-2","type":"TIME"}],"relations":[],"ambiguity":"MULTIPLE_EVENT_TIME_SCOPE","alternative_relations":[{"time_scope":"EVENT_1","status":"POSSIBLE"},{"time_scope":"EVENT_2","status":"POSSIBLE"}]}
    expected="ABSTAIN"
   if kind=="genitive":
    roles={"GENITIVE_HEAD":h,"GENITIVE_DEPENDENT":d}; spans={r:span(text,x) for r,x in roles.items()}
    for r,sp in spans.items():
     node_id="n-head" if r=="GENITIVE_HEAD" else "n-dependent"
     for node in graph["nodes"]:
      if node["id"]==node_id: node["source_span"]=sp
   else: roles={}; spans={}
   cases.append({"id":f"{lang}.{kind}.ambiguous.{i+1:02d}","language":lang,"target_construction":con,"gold_class":"AMBIGUOUS","text":text,"reference_graph":graph,"expected_role_bindings":roles,"expected_role_spans":spans,"expected_relation_type":"GENITIVE_UNSPECIFIED" if kind=="genitive" else None,"expected_status":expected,"generator":{"id":"usg.phase6.automatic-reference/1.0.0","seed":SEED,"scenario":"AMBIGUOUS"}})
  inventory[f"{lang}/{con}"]={"positive":20,"negative":20,"ambiguous":10}

 lexicon={"resource_id":"usg.phase6.synthetic-reference-lexicon","version":"1.0.0","license":"CC0-1.0","status":"BENCHMARK_ONLY","provenance":"Original project lexical seeds, generated independently of development fixtures and candidate lexicon.","entries":list(entries.values())}
 lex_text=json.dumps(lexicon,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
 corpus={"benchmark_id":"usg-phase6-automatic-synthetic-reference","version":"1.0.0","contract":"USG-INTERPRET/0.3.0","status":"SYNTHETIC_REFERENCE_BENCHMARK","license":"CC0-1.0","generation":{"method":"MEANING_GRAPH_FIRST_THEN_SEPARATE_LANGUAGE_REALIZATION","generator_id":"usg.phase6.automatic-reference/1.0.0","seed":SEED,"uses_human_annotations":False,"uses_model_labels":False,"reads_development_fixtures":False,"reads_candidate_lexicon":False,"candidate_predictions_used_during_generation":False,"external_corpus_dependency":None,"reference_lexicon_sha256":hashlib.sha256(lex_text.encode()).hexdigest(),"case_count":len(cases)},"limitations":["Controlled synthetic evidence only; not naturalistic human-annotated gold.","No general English or MSA accuracy claim is made.","Lexical seeds and phrase templates are deliberately bounded."],"construction_inventory":inventory,"minimums_per_profile":{"positive":20,"negative":20,"ambiguous":10},"cases":cases}
 return corpus,lexicon

def validate(corpus,lexicon):
 expected={f"{l}/{c}" for l,c in PROFILES}
 if set(corpus["construction_inventory"])!=expected or len(corpus["cases"])!=500: raise ValueError("profile inventory/case count mismatch")
 ids=[c["id"] for c in corpus["cases"]]
 if len(ids)!=len(set(ids)): raise ValueError("duplicate case IDs")
 for key in expected:
  rows=[c for c in corpus["cases"] if f"{c['language']}/{c['target_construction']}"==key]
  got={k:sum(c["gold_class"]==v for c in rows) for k,v in [("positive","POSITIVE"),("negative","NEGATIVE"),("ambiguous","AMBIGUOUS")]}
  if got!={"positive":20,"negative":20,"ambiguous":10}: raise ValueError(f"bad profile denominators {key}: {got}")
  same={}
  for c in rows:
   normalized=" ".join(c["text"].split()).casefold()
   if normalized in same and same[normalized]!=c["gold_class"]: raise ValueError(f"conflicting labels {key}: {normalized}")
   same[normalized]=c["gold_class"]
   for role,sp in c["expected_role_spans"].items():
    if c["text"][sp["start"]:sp["end"]]!=sp["surface"] or c["expected_role_bindings"][role]!=sp["surface"]: raise ValueError(f"bad span {c['id']}/{role}")
 if corpus["generation"]["uses_human_annotations"] or corpus["generation"]["uses_model_labels"] or corpus["generation"]["reads_development_fixtures"] or corpus["generation"]["reads_candidate_lexicon"]: raise ValueError("invalid benchmark provenance")
 if lexicon["license"]!="CC0-1.0": raise ValueError("reference lexicon must be CC0")

def main():
 corpus,lexicon=build(); validate(corpus,lexicon); OUT.mkdir(parents=True,exist_ok=True)
 (OUT/"corpus.json").write_text(json.dumps(corpus,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 (OUT/"reference-lexicon.json").write_text(json.dumps(lexicon,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
 print(json.dumps({"cases":len(corpus["cases"]),"profiles":len(corpus["construction_inventory"]),"lexicon_entries":len(lexicon["entries"])},indent=2))
if __name__=="__main__": main()
