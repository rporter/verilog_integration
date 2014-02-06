# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

include make.inc

VERILOG=../verilog
SCRIPT?=test_example
TIMEOUT?=3000

SIM_ARGS=+python+$(SCRIPT).py +timeout+$(TIMEOUT)
LIBEXM=../c/libexm_vpi

.PHONY : all build verilog iverilog verilate cver clean

all : iverilog icarus verilator verilate

iverilog icarus : iverilog-build $(LIBEXM).vpl
	PYTHONPATH=$$PYTHONPATH:. $(IRUN) -m $(LIBEXM) example.iverilog $(SIM_ARGS)

iverilog-build : build
	$(IBUILD) -g2005-sv -D IVERILOG -I$(VERILOG) $(VERILOG)/example.v -o example.iverilog

verilator verilate : verilog
	PYTHONPATH=$$PYTHONPATH:. $(VERILOG)/example/examplex $(SIM_ARGS)

../c/% :
	$(MAKE) -C ../c $(notdir $@)

regress : all
       ./regress

build :
	$(MAKE) -C ../c
	$(MAKE) -C ../db
	$(MAKE) -C ../python

verilog : build
	$(MAKE) -C ../verilog

clean :
	$(MAKE) -C ../c       clean
	$(MAKE) -C ../python  clean
	$(MAKE) -C ../verilog clean
	-@rm example.iverilog
