# Copyright (c) 2012 Rich Porter - see LICENSE for further details

include ../test/make.inc

CFLAGS+=-fPIC -ggdb
PY_LDFLAGS=$(shell python-config --libs)

.PHONY : all clean

all : libexm_vpi.so

libexm_vpi.so : exm_python.o exm_vpi.o exm_dpi.o message.o
	$(CXX) -export-dynamic -shared $^ -o $@ $(PY_LDFLAGS)

exm_python.o : exm_python.c exm_python.h
	$(CXX) $(CFLAGS) $(PY_CFLAGS) $(VL_CFLAGS) -DPYTHONDIR=\"$$PWD/../python\" -c $< -o $@

exm_%pi.o : exm_%pi.c
	$(CXX) $(CFLAGS) $(VL_CFLAGS) -c $< -o $@

message.o : message.cpp message.h
	$(CXX) $(CFLAGS) $(VL_CFLAGS) -c $< -o $@

clean :
	-@rm *.o *.so *~
