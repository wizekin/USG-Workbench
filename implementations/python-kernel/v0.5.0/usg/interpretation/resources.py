"""Installation-owned lexical resources. Ambiguous senses are never overwritten."""
import json
from pathlib import Path
from types import MappingProxyType

from ..concepts.lexicon import LexicalResolution, resolve
from ..util import canonical_json, sha256_hex


class LexicalResource:
    def __init__(self,body,ontology):
        if not isinstance(body,dict) or set(body)!={'resource_id','version','entries'}:
            raise ValueError('lexical resource schema')
        if not isinstance(body['resource_id'],str) or not 1<=len(body['resource_id'])<=100 or type(body['version']) is not int or body['version']<1:
            raise ValueError('lexical resource identity')
        if not isinstance(body['entries'],list) or len(body['entries'])>50000:
            raise ValueError('lexical resource capacity')
        entries={}
        for entry in body['entries']:
            if not isinstance(entry,dict) or set(entry)!={'language','form','concepts'}:
                raise ValueError('lexical entry schema')
            lang,form,concepts=entry['language'],entry['form'],entry['concepts']
            if lang not in {'en','ar'} or not isinstance(form,str) or not 1<=len(form)<=100 or not isinstance(concepts,list) or not 1<=len(concepts)<=8:
                raise ValueError('lexical entry limits')
            if any(not isinstance(c,str) or not ontology.has(c) for c in concepts):
                raise ValueError('resource refers to an uninstalled concept')
            key=(lang,form.casefold())
            if key in entries:
                raise ValueError('duplicate lexical entry')
            # Preserve the package's senses as well: a resource cannot remove
            # ambiguity or redefine an established word by replacing its entry.
            entries[key]=tuple(sorted(set(concepts)|set(resolve(form,lang).concepts)))
        self.entries=MappingProxyType(entries)
        self.body=json.loads(canonical_json(body))
        self.digest=sha256_hex(canonical_json(body))

    @classmethod
    def load(cls,path,ontology):
        with open(path,'rb') as f:raw=f.read(8_000_001)
        if len(raw)>8_000_000:
            raise ValueError('lexical resource size')
        from ..encoding.usbf import _json
        return cls(_json(raw),ontology)

    def resolve(self,form,language='en'):
        concepts=self.entries.get((language,form.casefold()),resolve(form,language).concepts)
        return LexicalResolution(form,concepts,'RESOLVED' if len(concepts)==1 else 'AMBIGUOUS' if concepts else 'UNRESOLVED')
