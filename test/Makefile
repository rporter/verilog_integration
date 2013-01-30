# Copyright (c) 2012 Rich Porter - see LICENSE for further details

include make.inc

VERILOG=../verilog
SCRIPT?=example
TIMEOUT?=3000

SIM_ARGS=+python+$(VERILOG)/$(SCRIPT).py +timeout+$(TIMEOUT)

.PHONY : all build verilog iverilog verilate cver clean

all : iverilog verilate

iverilog : iverilog-build
	$(IRUN) -m ../c/libexm_vpi.so example.iverilog $(SIM_ARGS)

iverilog-build : build
	$(IBUILD) -g2005-sv -I$(VERILOG) $(VERILOG)/example.v -o example.iverilog

verilate : verilog
	$(VERILOG)/example/examplex $(SIM_ARGS)

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
