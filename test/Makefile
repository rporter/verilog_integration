# Copyright (c) 2012 Rich Porter - see LICENSE for further details

include make.inc

VERILOG=../verilog

.PHONY : build verilog iverilog verilate cver clean

iverilog : iverilog-build
	$(IRUN) -m ../c/libexm_vpi.so example.iverilog +python+$(VERILOG)/example.py +timeout+3000

iverilog-build : build
	$(IBUILD) -g2005-sv -I$(VERILOG) $(VERILOG)/example.v -o example.iverilog

verilate : verilog
	$(VERILOG)/example/examplex +python+$(VERILOG)/example.py +timeout+3000

build :
	$(MAKE) -C ../c
	$(MAKE) -C ../python

verilog : build
	$(MAKE) -C ../verilog

clean :
	$(MAKE) -C ../c       clean
	$(MAKE) -C ../python  clean
	$(MAKE) -C ../verilog clean
