# Copyright (c) 2012 Rich Porter - see LICENSE for further details

include ../test/make.inc

VL_FLAGS=--cc example.v -DEXM_USE_DPI -no-l2name

.PHONY : all verilate compile clean

all : verilate compile

include $(VERILATOR_ROOT)/include/verilated.mk

verilate :
	$(VERILATOR_ROOT)/bin/verilator $(VL_FLAGS) example.cpp

compile:
	cd obj_dir ; $(MAKE) -f ../Makefile_obj

clean :
	rm -rf obj_dir *~ *.pyc
