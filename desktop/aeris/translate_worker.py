"""Optional Argos adapter. No model installation; deny Python socket network operations.
Not an OS sandbox. Real engine requires separate review and offline validation.
"""
import json
import os
import sys
from aeris.translate import validate

def deny_network(event, args):
    if event.startswith('socket.'):
        raise PermissionError('Network disabled in translation worker')

def main():
    # Prevent user configuration from selecting a remote provider.
    os.environ.update(ARGOS_MODEL_PROVIDER='OPENNMT', ARGOS_DEVICE_TYPE='cpu',
                      ARGOS_CHUNK_TYPE='MINISBD', ARGOS_DEBUG='0')
    sys.addaudithook(deny_network)
    try:
        request=json.loads(sys.stdin.read(60000))
        text,source,target=(request[k] for k in ('text','source','target'))
        validate(text,source,target)
        # Do not expose engine diagnostics or user text to output logs.
        from contextlib import redirect_stdout
        with redirect_stdout(sys.stderr):
            from argostranslate import translate
            a=translate.get_language_from_code(source)
            b=translate.get_language_from_code(target)
            route=a.get_translation(b) if a and b else None
            if route is None: raise ValueError('Missing local model')
            result=route.translate(text)
        if not isinstance(result,str) or len(result)>40000: raise ValueError('Invalid output')
        print(json.dumps({'ok':True,'text':result},ensure_ascii=True))
    except Exception:
        print(json.dumps({'ok':False}))

if __name__=='__main__': main()
