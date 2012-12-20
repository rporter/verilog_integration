# Copyright (c) 2012 Rich Porter - see LICENSE for further details

VERILOG=../verilog

.PHONY : all test clean

test : all
	$(VERILOG)/example/examplex +python+$(VERILOG)/example.py +timeout+3000

all :
	$(MAKE) -C ../c
	$(MAKE) -C ../python
	$(MAKE) -C ../verilog

clean :
	$(MAKE) -C ../c       clean
	$(MAKE) -C ../python  clean
	$(MAKE) -C ../verilog clean
