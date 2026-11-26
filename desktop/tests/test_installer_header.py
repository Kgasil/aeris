import io
import struct
import unittest

from aeris.release_check import pe_installer


def header(machine=0x14c, offset=128):
    data=bytearray(152)
    data[:2]=b'MZ'
    struct.pack_into('<I',data,60,offset)
    data[128:132]=b'PE\0\0'
    struct.pack_into('<H',data,132,machine)
    return bytes(data)


class InstallerHeaderTests(unittest.TestCase):
    def test_supported_bootstrappers(self):
        for machine in (0x14c,0x8664):
            pe_installer(io.BytesIO(header(machine)))

    def test_truncated_header(self):
        for data in (b'MZ',header()[:130],b'fake'):
            with self.subTest(data=data[:8]), self.assertRaises(ValueError):
                pe_installer(io.BytesIO(data))

    def test_bad_offset(self):
        for offset in (0,63,1024*1024+1):
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                pe_installer(io.BytesIO(header(offset=offset)))

    def test_wrong_machine(self):
        with self.assertRaises(ValueError):
            pe_installer(io.BytesIO(header(0xaa64)))


if __name__=='__main__':
    unittest.main()
