# Copyright (c) 2012 Rich Porter - see LICENSE for further details

include ../test/make.inc

CFLAGS+=-fPIC
PY_LDFLAGS=$(shell python-config --libs)
IV_LDFLAGS=-L$(IVERILOG_ROOT)/lib -lvpi -lveriuser

.PHONY : all clean

all : libexm_vpi.so

libexm_vpi.so : exm_python.o exm_vpi.o
	$(CXX) -export-dynamic -shared $^ -o $@ $(PY_LDFLAGS) $(IV_LDFLAGS)

exm_python.o : exm_python.c exm_python.h
	$(CXX) $(CFLAGS) $(PY_CFLAGS) $(VL_CFLAGS) -DPYTHONDIR=\"$$PWD/../python\" -c $< -o $@

exm_vpi.o : exm_vpi.c
	$(CXX) $(CFLAGS) $(VL_CFLAGS) -c $< -o $@

clean :
	-@rm *.o *.so *~
