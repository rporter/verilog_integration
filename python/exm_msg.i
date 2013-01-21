// Copyright (c) 2012 Rich Porter - see LICENSE for further details

%module exm_msg

%{
#include "message.h"
%}

%ignore example::message::emit(unsigned int level, char* severity, char *file, unsigned int line, char* text, va_list args);

/* Parse the header file to generate wrappers */
%include "message.h"
