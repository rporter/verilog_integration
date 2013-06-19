# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

include ../test/make.inc

CFLAGS+=-fPIC -ggdb
PY_LDFLAGS=$(shell python-config --libs) -lrt
LDFLAGS+=-lrt -lboost_regex

.PHONY : all clean

all : libexm_vpi.so libmessage.so

libexm_vpi.so : exm_python.o exm_vpi.o exm_dpi.o message.o exm_msg.o
	$(CXX) -export-dynamic -shared $^ -o $@ $(PY_LDFLAGS) $(LDFLAGS)

libexm_vpi.vpl : libexm_vpi.so
	ln -s $^ $@

libmessage.so : message.o
	$(CXX) -export-dynamic -shared $< -o $@ $(LDFLAGS)

exm_python.o : exm_python.c exm_python.h
	$(CXX) $(CFLAGS) $(PY_CFLAGS) $(VL_CFLAGS) -DPYTHONDIR=\"$(ROOT)/python\" -c $< -o $@

exm_%pi.o : exm_%pi.c
	$(CXX) $(CFLAGS) $(VL_CFLAGS) -c $< -o $@

exm_verilated.o : exm_verilated.cpp
	$(CXX) $(CFLAGS) $(VL_CFLAGS) -c $< -o $@

exm_msg.o : exm_msg.cpp
	$(CXX) $(CFLAGS) $(VL_CFLAGS) -c $< -o $@

message.o : message.cpp message.h
	$(CXX) $(CFLAGS) $(VL_CFLAGS) -c $< -o $@

clean :
	-@rm *.o *.so *.vpl *~
