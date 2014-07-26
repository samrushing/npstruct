
npstruct
========

This is a 'non-packing struct' module, written ~1996.  Back then I
think Python's struct module couldn't be used to pack without using
C's alignment/packing rules, and I also needed some of the other
features like callbacks and bitfields.

This module (especially the 'oracle' class) was used in my 'Dynwin'
project, a swing-like UI built in pure python.  Today this would be
done using ctypes.
