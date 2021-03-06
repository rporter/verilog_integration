// Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

#include "message.h"

// use c linkage
extern "C" {
  void exm_int_debug  (const char* formatted);
  void exm_debug      (const char* formatted);
  void exm_information(const char* formatted);
  void exm_note       (const char* formatted);
  void exm_warning    (const char* formatted);
  void exm_success    (const char* formatted);
  void exm_error      (const char* formatted);
  void exm_internal   (const char* formatted);
  void exm_fatal      (const char* formatted);
}
