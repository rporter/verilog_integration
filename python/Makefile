# Copyright (c) 2012 Rich Porter - see LICENSE for further details

include ../test/make.inc

.PHONY : vpi clean

vpi : _vpi.so _exm_msg.so

exm_msg_wrap.cxx : exm_msg.i ../c/message.cpp ../c/message.h
	swig -python -c++ -I../c $<

vpi_wrap.c : vpi.i
	swig -python -I$(VERILATOR_INC) $<

exm_msg_wrap.o : exm_msg_wrap.cxx
	$(CXX) -fpermissive -fPIC $(CFLAGS) -I../c $(PY_CFLAGS) $(VL_CFLAGS) -c $<

vpi_wrap.o : vpi_wrap.c
	$(CC) -fPIC $(CFLAGS) $(PY_CFLAGS) $(VL_CFLAGS) -c $<

_%.so : %_wrap.o
	$(CXX) -export-dynamic -shared $< $(PY_LDFLAGS) -L ../c -Wl,-rpath=$(ROOT)/c -lmessage -o $@

clean :
	-@rm *.o *.so vpi.py exm_msg.py *_wrap.c* *~
