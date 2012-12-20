# Copyright (c) 2012 Rich Porter - see LICENSE for further details

include ../test/make.inc

.PHONY : vpi clean

vpi : _vpi.so

%_wrap.c : %.i
	swig -python -I$(VERILATOR_INC) $<

%_wrap.o : %_wrap.c
	$(CC) -fPIC $(CFLAGS) $(PY_CFLAGS) $(VL_CFLAGS) -c $<

_%.so : %_wrap.o
	$(CC) -export-dynamic -shared $< $(PY_LDFLAGS) -o $@

clean :
	-@rm *.o *.so vpi.py *_wrap.c *~
