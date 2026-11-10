import random
import unittest
from usg.encoding.compact import dumps,loads,schemas_from_library
from usg.encoding.usbf import encode,decode,DecodeError
from usg.foundation.builder import build_foundation
from usg.grammar.node import apply,ref,hole
from usg.grammar.serialize import node_to_json


class CompactTests(unittest.TestCase):
    def setUp(self):self.schemas=schemas_from_library(build_foundation().frames)

    def test_all_hole_states_absent_roles_and_annotations(self):
        for state in ('UNKNOWN','UNSPECIFIED','WITHHELD','NOT_APPLICABLE'):
            x=node_to_json(apply('GIVE',1,{'AGENT':ref('REFERENT:1'),'SOURCE':ref('REFERENT:1'),'THEME':hole(state)}))
            self.assertEqual(loads(dumps(x,self.schemas)),x)
            self.assertEqual(decode(encode([x],codec='compact',schemas=self.schemas)),[x])

    def test_repeated_instances_are_preserved(self):
        x=node_to_json(apply('OPEN',1,{'UNDERGOER':ref('REFERENT:1')}))
        self.assertEqual(loads(dumps([x,x],self.schemas)),[x,x])

    def test_generic_types_and_unicode(self):
        x={'x':[None,True,False,-9223372036854775808,1.25,'العربية 😃'], 'y':{}}
        self.assertEqual(loads(dumps(x)),x)

    def test_unknown_frames_fall_back_without_loss(self):
        x=node_to_json(apply('FUTURE_FRAME',5,{'X':ref('REFERENT:8')}))
        self.assertEqual(loads(dumps(x,self.schemas)),x)

    def test_truncation_and_hostile_mutations(self):
        data=dumps([node_to_json(apply('OPEN',1,{'UNDERGOER':hole()}))],self.schemas)
        for n in range(len(data)):
            with self.assertRaises(DecodeError):loads(data[:n])
        rng=random.Random(500)
        for _ in range(300):
            b=bytearray(data);b[rng.randrange(len(b))]^=rng.randrange(1,256)
            try:loads(bytes(b))
            except DecodeError:pass

    def test_trailing_bytes_and_unknown_critical_tags(self):
        with self.assertRaises(DecodeError):loads(dumps(1)+b'\x00')
        with self.assertRaises(DecodeError):loads(b'CIR1\x00\x00\xff')


if __name__=='__main__':unittest.main()
