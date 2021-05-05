#!/usr/bin/env python3

import ocrmypdf
import inspect

sig = inspect.signature(ocrmypdf.ocr)
#print (str(sig))
for param in sig.parameters.values():
    if (param.kind == param.KEYWORD_ONLY):
        print('Parameter:', param)
