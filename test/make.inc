# Copyright (c) 2012 Rich Porter - see LICENSE for further details

PY_LDFLAGS?=$(shell python-config --libs)
PY_CFLAGS?=$(shell python-config --includes)

TOOL_ROOT=/enalvo/ap

CVER_HOME?=$(TOOL_ROOT)/cver/2.12a-p3

#VERILATOR_ROOT?=$(TOOL_ROOT)/verilator/3.844-dev
VERILATOR_ROOT?=/enalvo/work/rporter/3.844-dev
VERILATOR_INC?=$(VERILATOR_ROOT)/include
VERILATOR?=$(VERILATOR_ROOT)/bin/verilator
VL_CFLAGS?=-I$(VERILATOR_INC) -I$(VERILATOR_INC)/vltstd

export VERILATOR_ROOT
