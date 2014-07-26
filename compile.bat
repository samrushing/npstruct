gcc -I../Include -O2 -c npstructmodule.c -o npstructmodule.o
dllwrap --dllname npstruct.pyd --driver-name gcc --def npstruct.def -o npstruct.pyd npstructmodule.o -s --entry _DllMain@12 --target=i386-mingw32 -L../libs -lpython24
