"""Small explicit lexical resource. A label match is a lexical link, not identity proof."""
from dataclasses import dataclass


FORMS = {
    "Person": "person people man woman boy girl child john mary alice bob james tom sarah",
    "Doctor": "doctor physician doctors physicians", "Patient": "patient patients",
    "Medication": "medication medicine drug medications drugs", "Tablet": "tablet pill tablets pills",
    "Apple": "apple apples", "Food": "food bread meal rice", "Book": "book books",
    "Door": "door doors", "Car": "car cars automobile automobiles", "Vehicle": "vehicle vehicles",
    "Pump": "pump pumps", "Heart": "heart hearts", "Blood": "blood", "Water": "water",
    "Pipe": "pipe pipes", "BloodVessel": "vessel vessels", "Telescope": "telescope telescopes",
    "Hospital": "hospital hospitals", "Company": "company companies", "Information": "information message news file data",
    "Money": "money dollar dollars euro euros", "Location": "room home school park city office london cairo",
    "Organization": "organization organisation", "Artifact": "ball box key computer", "Animal": "dog cat horse bird",
    "Argument": "argument arguments", "Device": "device devices", "Substance": "ice steam",
}
ARABIC = {"طبيب": "Doctor", "الطبيب": "Doctor", "مريض": "Patient", "المريض": "Patient",
          "دواء": "Medication", "الدواء": "Medication", "تفاحة": "Apple", "التفاحة": "Apple",
          "ولد": "Person", "الولد": "Person", "بنت": "Person", "البنت": "Person",
          "باب": "Door", "الباب": "Door", "كتاب": "Book", "الكتاب": "Book",
          "ماء": "Water", "الماء": "Water", "قلب": "Heart", "القلب": "Heart"}
LEXICON = {word: (concept,) for concept, words in FORMS.items() for word in words.split()}
LEXICON["bank"] = ("Organization", "Location")

# A package-authored semantic alignment is required before a learned literal
# alias can activate. Model-provided examples cannot certify their own meaning.
VETTED_VERB_ALIASES = {"consumed": "ate", "devoured": "ate", "examines": "examines"}


@dataclass(frozen=True)
class LexicalResolution:
    form: str
    concepts: tuple[str, ...]
    outcome: str


def resolve(form, language="en"):
    key = form.casefold()
    if language=='ar':key=''.join(c for c in key if not ('\u064b'<=c<='\u0652' or c in {'\u0670','\u0640'}))
    concepts = LEXICON.get(key, ()) if language == "en" else ((ARABIC[key],) if key in ARABIC else ())
    return LexicalResolution(form, concepts, "RESOLVED" if len(concepts) == 1 else "AMBIGUOUS" if concepts else "UNRESOLVED")
