# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

PY_LDFLAGS?=$(shell python-config --libs)
PY_CFLAGS?=$(shell python-config --includes)

ROOT?=$(shell dirname $$PWD)

TOOL_ROOT?=/opt/ap

IVERILOG_ROOT=$(TOOL_ROOT)/iverilog/20130307
IBUILD=$(IVERILOG_ROOT)/bin/iverilog
IRUN=$(IVERILOG_ROOT)/bin/vvp

VERILATOR_ROOT?=$(TOOL_ROOT)/verilator/3.846
VERILATOR_INC?=$(VERILATOR_ROOT)/include
VERILATOR?=$(VERILATOR_ROOT)/bin/verilator
VL_CFLAGS?=-I$(VERILATOR_INC) -I$(VERILATOR_INC)/vltstd

export VERILATOR_ROOT
