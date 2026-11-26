# Upstream notices — candidate Python 3.14.10

Collected from the [CPython 3.14.10 external dependency list](https://github.com/python/cpython/blob/v3.14.10/PCbuild/get_externals.bat) and corresponding upstream versioned sources. These are unmodified upstream texts, not an Aeris license or final redistribution approval. Candidate CI copies the ten .txt files below and the actual Inno Setup 6.7.4 license into NOTICES before computing the manifest.

| File | Source |
|---|---|
| OpenSSL-3.5.9.txt | [CPython dependency source](https://github.com/python/cpython-source-deps/blob/openssl-3.5.9/LICENSE.txt) |
| bzip2-1.0.8.txt | [CPython dependency source](https://github.com/python/cpython-source-deps/blob/bzip2-1.0.8/LICENSE) |
| libffi-3.4.4.txt | [CPython dependency source](https://github.com/python/cpython-source-deps/blob/libffi-3.4.4/LICENSE) |
| XZ-5.2.5.txt | [CPython dependency source](https://github.com/python/cpython-source-deps/blob/xz-5.2.5/COPYING) |
| XZ-5.2.5-COPYING.LGPLv2.1.txt | [CPython dependency source](https://github.com/python/cpython-source-deps/blob/xz-5.2.5/COPYING.LGPLv2.1) |
| Zstandard-1.5.7.txt | [CPython dependency source](https://github.com/python/cpython-source-deps/blob/zstd-1.5.7/LICENSE) |
| zlib-ng-2.2.4.txt | [CPython dependency source](https://github.com/python/cpython-source-deps/blob/zlib-ng-2.2.4/LICENSE.md) |
| zlib-1.3.2.txt | [zlib upstream](https://github.com/madler/zlib/blob/v1.3.2/LICENSE) |
| mpdecimal-4.0.0.txt | [CPython dependency source](https://github.com/python/cpython-source-deps/blob/mpdecimal-4.0.0/COPYRIGHT.txt) |
| libexpat.txt | [CPython 3.14.10 vendored Expat](https://github.com/python/cpython/blob/v3.14.10/Modules/expat/COPYING) |

Remaining: identify exact Unicode data and libtommath provenance and notices; review Tcl/Tk embedded resources and dependencies, OpenSSL notices, actual XZ/liblzma files and applicable licenses, Microsoft redistribution rights and first-party terms. Verify actual files and hashes from the next candidate; collection alone does not close any legal or security gate. No release authorization.

Additional collected texts: `libtommath-tcl-9.0.4.txt` from [Tcl's vendored LibTomMath](https://github.com/python/cpython-source-deps/blob/tcl-9.0.4.0/libtommath/LICENSE) and `Unicode-16.0.0.txt` from [Unicode Consortium source](https://github.com/unicode-org/unicodetools/blob/main/LICENSE). CPython 3.14.10 [generated Unicode database](https://github.com/python/cpython/blob/v3.14.10/Modules/unicodedata_db.h) declares 16.0.0. Verify the exact bundled LibTomMath version, legacy Unicode data and applicable terms; these texts are not a complete legal determination. CI commit 980c8f5 adds both notices and checks installed/reinstalled notice hashes; results pending.
