import unittest
from pathlib import Path
from check_microsoft_runtime import verify,read,EXPECTED
class RuntimeTests(unittest.TestCase):
    def test_verified_exact_map_only(self):
        source=read(Path(__file__).parents[0]/"microsoft-source-evidence.json")
        rows=[{"path":"_internal/"+n,"sha256":h,"authenticode":"Valid"} for n,h in EXPECTED.items()]
        red={"remaining_vcruntime":[{"name":n,"sha256":h,"python_source_sha256":h,"exact_python_match":True} for n,h in EXPECTED.items()]}
        self.assertFalse(verify(source,rows,red)["release_approved"])
        for bad in [rows[:-1],rows+[dict(rows[0])],rows+[{"path":"_internal/msvcp140.dll","sha256":"a"*64,"authenticode":"Valid"}],[dict(rows[0],sha256="b"*64),rows[1]],[dict(rows[0],authenticode="NotSigned"),rows[1]]]:
            with self.assertRaises(ValueError):verify(source,bad,red)
        with self.assertRaises(ValueError):verify(dict(source,artifact_id=1),rows,red)
if __name__=="__main__":unittest.main()
