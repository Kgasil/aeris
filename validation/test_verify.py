import hashlib,json,os,unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from aeris.verify import hash_file,expected_hash,Cancelled,CHUNK
from aeris.settings import Settings,Appearance

class VerifyTests(unittest.TestCase):
    def test_vectors(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'a'; p.write_bytes(b'abc')
            for alg,fn in [('SHA-256',hashlib.sha256),('SHA-512',hashlib.sha512)]:
                digest=fn(b'abc').hexdigest(); self.assertEqual(hash_file(p,alg).digest,digest)
                self.assertTrue(hash_file(p,alg,digest.upper()).matches)
                self.assertFalse(hash_file(p,alg,'0'*len(digest)).matches)
                self.assertEqual(p.read_bytes(),b'abc')
    def test_invalid(self):
        for alg,value in [('MD5',''),('SHA-256','0'*63),('SHA-512','z'*128)]:
            with self.assertRaises(ValueError): expected_hash(alg,value)
    def test_blocks_and_empty(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'a'; data=b'a'*(CHUNK*2+7); p.write_bytes(data); calls=[]
            self.assertEqual(hash_file(p,'SHA-256',progress=lambda a,b:calls.append(a)).digest,hashlib.sha256(data).hexdigest())
            self.assertEqual(calls,[0,CHUNK,CHUNK*2,len(data)])
            p.write_bytes(b''); self.assertEqual(hash_file(p,'SHA-512').size,0)
    def test_cancel_and_change(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'a'; p.write_bytes(b'a'*(CHUNK+1)); flag=[False]
            with self.assertRaises(Cancelled): hash_file(p,'SHA-256',cancelled=lambda:flag[0],progress=lambda a,b:flag.__setitem__(0,a>0))
            def change(a,b):
                if a==CHUNK:
                    with p.open('ab') as f: f.write(b'!')
            with self.assertRaises(ValueError): hash_file(p,'SHA-256',progress=change)
    def test_nonregular(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(ValueError): hash_file(d,'SHA-256')
            with self.assertRaises(OSError): hash_file(Path(d)/'missing','SHA-256')
            if os.name!='nt':
                p=Path(d)/'fifo'; os.mkfifo(p)
                with self.assertRaises(ValueError): hash_file(p,'SHA-256')
                q=Path(d)/'link'; q.symlink_to(p)
                with self.assertRaises(ValueError): hash_file(q,'SHA-256')
    def test_replacement_at_open_boundary(self):
        from aeris.verify import _open_read, _matches_path
        with TemporaryDirectory() as d:
            p=Path(d)/'original'; replacement=Path(d)/'replacement'
            p.write_bytes(b'abc'); replacement.write_bytes(b'abc')
            before=p.lstat()
            with os.fdopen(_open_read(p),'rb') as f:
                initial=os.fstat(f.fileno())
                self.assertTrue(_matches_path(p,before,f,initial))
                try:
                    os.replace(replacement,p)
                except PermissionError as exc:
                    # Windows may deny replacement of an open file even when
                    # the handle permits delete sharing. Verify nothing changed.
                    if os.name != 'nt' or getattr(exc, 'winerror', None) not in (5, 32):
                        raise
                    self.assertTrue(replacement.exists())
                    self.assertTrue(_matches_path(p,before,f,initial))
                else:
                    self.assertFalse(_matches_path(p,before,f,initial))
            # Also check a completed replacement independently of open-handle
            # rename semantics on the underlying filesystem.
            replacement.write_bytes(b'longer replacement')
            os.replace(replacement,p)
            with os.fdopen(_open_read(p),'rb') as f:
                self.assertFalse(_matches_path(p,before,f,os.fstat(f.fileno())))

    def test_migration(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'settings.json'; s=Settings(p); s.set_module('Link',True)
            data=json.loads(p.read_text()); data['schema']=21; del data['verify_enabled']; p.write_text(json.dumps(data))
            s=Settings(p); self.assertFalse(s.warning); self.assertTrue(s.link_enabled); self.assertFalse(s.verify_enabled)
            s.set_module('Verify',True); s.set_appearance(Appearance(favorites=('Verify',)))
            self.assertTrue(Settings(p).verify_enabled)
