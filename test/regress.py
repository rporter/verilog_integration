# Copyright (c) 2012, 2013 Rich Porter - see LICENSE for further details

import libxml2
import mdb
import message
import os
import subprocess
import sys

################################################################################

def increase_verbosity(option, opt, value, parser) :
  parser.values.verbosity -= 1

parser = message.reportOptionParser()
parser.add_option('-s', '--subset', default=None, help='Test subset', action='append')
parser.add_option('-r', '--root', help='root directory')
parser.add_option('', '--verbosity', help='set absolute verbosity', default=message.INFORMATION)
parser.add_option('-v', '', help='increase verbosity', action='callback', callback=increase_verbosity)
parser.add_option('-x', '--xml', help='set regression xml description', default='test/regress.xml')
options, values = parser.parse_args()

################################################################################

mdb.db.connection.set_default_db(db='../db/mdb.db', root=options.root)
message.message.verbosity(options.verbosity)
m=mdb.mdb('regress', activity='regression')

################################################################################

class regression :
  def __init__(self, xml) :
    try :
      self.xml = libxml2.parseFile(xml)
    except :
      message.fatal('unable to read regression file %(xml)s because %(excpt)s', xml=xml, excpt=sys.exc_info()[1])
      return
    for idx, node in enumerate(self.xml.xpathEval('//*')) :
      try :
        node.setProp('nid', 'id-' + str(idx))
      except :
        message.debug('setProp failed for %(tag)s', tag=node.name)

  def getopt(self, opt, node, default=None) :
    try :
      return node.xpathEval('ancestor-or-self::*/option/%s/text()[1]' % opt)[0].getContent()
    except :
      return default

  def enqueue(self, cmd) :
    'just execute here'
    message.debug('enqueue %(cmd)s', cmd=cmd)
    result = subprocess.Popen(cmd.split(' '), env={'MDB': 'root='+str(m.get_root())+',parent='+str(m.log_id)}).wait()
    if result > 0 :
      message.note('process %(cmd)s returned non zero %(result)d', cmd=cmd, result=result)

  def run(self, subset) :
    if subset is None :
      self.tree(self.xml.getRootElement())
    else :
      for node in subset :
        for node in self.xml.xpathEval('//*[@name="%s" or @nid="%s"]' % (node, node)) :
          self.tree(node)

  def tree(self, node) :
    for child in node.xpathEval('child::*[not(@ignore)]') :
      if child.name == 'test' :
        self.enqueue('make -C test ' + self.getopt('target', child) + ' SCRIPT=test_' + child.getContent())
      else :
        self.enqueue('echo ' + child.name)

################################################################################

suite=regression(options.xml)
suite.run(options.subset)

################################################################################

mdb.finalize_all()
