# Copyright (c) 2013 Rich Porter - see LICENSE for further details

import os
import random
import re
import subprocess
import xml.etree.ElementTree as etree

import coverage
import database
import mdb
import message
import test
import utils

################################################################################

#message.message.verbosity(message.INT_DEBUG)

################################################################################

choices = (False,)*10 + (True,)

class coverpoint(coverage.coverpoint) :
  'stuff'
  NAMES='abcdefghijklmnopqrstuvwxyz'
  def __init__(self, name) :
    for axis in random.sample(self.NAMES, random.randrange(2, self.number_of_axes)) :
      self.add_axis(axis, values=range(0, random.randrange(5, 10)))
    coverage.coverpoint.__init__(self, name=name)

  def define(self, bucket) :
    'set goal'
    # no dont cares or illegals
    bucket.default(goal=random.randrange(1, 100), dont_care=random.choice(choices), illegal=random.choice(choices))
  
  @utils.lazyProperty
  def number_of_axes(self) :
    limit = len(self.NAMES)
    result = test.test.plusarg_opt_int('max_axes', 3, 'd')
    if result < 1 :
      result = 1
    if result > limit : 
      result = limit
      message.warning('limit of %(limit)d axes', limit=limit)
    return result+1

################################################################################

class baseList :
  class test :
    def __init__(self, file, **args) :
      self.file = file
      self.args = args
    def __str__(self) :
      return 'python ' + self.file + ' ' + ' '.join('+%s=%s' % i for i in self.args.items())
  
  def __iter__(self) :
    for test in self.tests :
      yield str(test)

class randomList(baseList) :
  def __init__(self, count, seed, testnames, **args) :
    # set per run seed
    random.seed(seed)
    self.tests = [self.test(random.choice(testnames), tst_seed=str(random.randint(0,1<<30)), idx=idx, **args) for idx in range(0, count)]

class xmlList(baseList) :
  def __init__(self, xmlfile, **args) :
    def _test(node) :
      file, seed = node.find('test').text.split('-')
      return self.test(file, tst_seed=seed, **args)
    xml = etree.parse(xmlfile)
    self.tests = [_test(test) for test in xml.findall('./test')]

################################################################################

class thistest(test.test) :
  activity='python'
  block='default'
  name='multiple coverage capacity test'

  def prologue(self):
    # initialize all the same
    random.seed(self.cvr_seed)
    self.cpts = [coverpoint('%d random coverpoint' % i).cursor() for i in range(0, self.instances)]
    self.master_id = test.plusargs().master_id
  
  def epilogue(self) :

    def enqueue(cmd) :
      'just execute here'
      message.debug('enqueue %(cmd)s', cmd=cmd)
      result = subprocess.Popen(cmd.split(' '), env=dict(os.environ, MDB='root='+str(self.mdb.get_root())+',parent='+str(self.mdb.log_id))).wait()
      if result > 0 :
        message.warning('process %(cmd)s returned non zero %(result)d', cmd=cmd, result=result)
    
    if self.is_master :
      # spawn some children
      for test in self.tests() :
        enqueue(str(test))
      database.rgr().result(self.mdb.log_id, self.mdb.is_root()).summary().summary()
      # optimize ...
      optimize = database.cvgOrderedOptimize(log_ids=[self.mdb.log_id,])
      coverage.messages.hush_creation()
      # do optimize run
      xml = optimize.run()
      # ... and annotate coverage summary
      if self.coverage :
        self.coverage.load(optimize.dump())
    else :
      # set per run seed
      random.seed(self.tst_seed)
      # ignore illegal bucket hits
      coverage.messages.CVG_200.level = message.IGNORE
      # make some coverage
      for i in range(0, 9999) :
        with random.choice(self.cpts) as cursor :
          for name, axis in cursor.point.axes() :
            cursor(**{name : self.choice(self.choices[id(cursor)][name])})
          cursor.incr(random.randrange(10))
    # if everything else ok
    self.success()

  @utils.lazyProperty
  def choices(self) :
    'pick axis values to hit'
    def sample(values) : return sorted(random.sample(values, len(values)-1))
    return dict([(id(cursor), dict([(name, sample(axis.get_values())) for name, axis in cursor.point.axes()])) for cursor in self.cpts])

  def choice(self, opts) :
    return random.choice(opts)

  def tests(self) :
    args = dict(master_id=str(self.master_id or self.mdb.log_id), cvr_seed=str(self.cvr_seed), instances=str(self.instances))
    if test.plusargs().test_xml :
      return xmlList(test.plusargs().test_xml, **args)
    else :
      return randomList(self.children, self.tst_seed, self.testnames, **args)

  @property
  def test(self) :
    return self.filename()+'-'+str(hex(self.tst_seed))
  @utils.lazyProperty
  def is_master(self) :
    try :
      return int(test.plusargs().master)
    except :
      return self.mdb.is_root()

  @utils.lazyProperty
  def cvr_seed(self) :
    return self.plusarg_opt_int('cvr_seed', 0, '08x')
  @utils.lazyProperty
  def tst_seed(self) :
    return self.plusarg_opt_int('tst_seed', 0, '08x')
  @utils.lazyProperty
  def children(self) :
    return self.plusarg_opt_int('children', 20, 'd')
  @utils.lazyProperty
  def instances(self) :
    return self.plusarg_opt_int('instances', 20, 'd')
  @utils.lazyProperty
  def testnames(self) :
    return re.split(r'[+:,]', test.plusargs().get('tests', self.filename()))

################################################################################

if __name__ == '__main__' :
  thistest()
