import pkg_resources
from enum import Enum

class BattleType(Enum):
  arena = 0
  env = 1
  agent = 2

class BattleSpec(object):
  def __init__(self, id, type, entry_point=None, tags=None, **kwargs):
    self._id = self._check_id(id)
    self._type = self._check_type(type)
    self._entry_point = entry_point
    self._kwargs = kwargs
    self._tags = {} if tags is None else tags

  def make(self, *args, **kwargs):
    if len(kwargs) is None:
      kwargs_merge = self._kwargs
    else:
      kwargs_merge = self._kwargs
      kwargs_merge.update(kwargs)

    if self._entry_point is None:
      raise Exception("entry_point is null")
    elif callable(self._entry_point):
      return self._entry_point()
    else:
      entry_point = pkg_resources.EntryPoint.parse('x={}'.format(self._entry_point))
      print('entry_point=', entry_point, ",kwargs=", kwargs_merge)
      cls = entry_point.load(False)
      print('cls=', cls)
      return cls(*args, **kwargs_merge)

  def _check_type(self, type):
    return type

  def _check_id(self, id):
    return id

  @property
  def id(self):
    return self._id

  @property
  def type(self):
    return self._type

  @property
  def tags(self):
    return self._tags

  @property
  def def_kwargs(self):
    return self._kwargs


class BattleRegistry:
  def __init__(self):
    self._instances = {}

  def make(self, id, *args, **kwargs):
    spec = self.spec(id)
    if spec is None:
      raise Exception("spec {} un-register".format(id))
    return spec.make(*args, **kwargs)

  def ids(self, type=None):
    if type is None:
      return self._instances.keys()
    rst = list()
    for (k,v) in self._instances.items():
      if type == v.type:
        rst.append(k)
    return rst

  def specs(self, type=None):
    if type is None:
      return self._instances.values()
    rst = list()
    for v in self._instances.values():
      if type == v.type:
        rst.append(v)
    return rst

  def spec(self, id):
    if id in self._instances:
      return self._instances[id]
    else:
      return None

  def register(self, id, type, *args, **kwargs):
    if id in self._instances:
      raise Exception("repeat id {}".format(id))
    self._instances[id] = BattleSpec(id, type, *args, **kwargs)

registry = BattleRegistry()

def register(id, type, *args, **kwargs):
  return registry.register(id, type, *args, **kwargs)

def make(id, *args, **kwargs):
  return registry.make(id, *args, **kwargs)

def ids(type=None):
  return registry.ids(type)

def spec(id):
  return registry.spec(id)
