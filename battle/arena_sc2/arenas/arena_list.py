from battle.arena_sc2 import BattleType, make, ids, spec

import battle.arena_sc2.arenas
#import battle.arena_sc2.envs
#import battle.arena_sc2.agents

from absl import app

def list_arena_spec(unused_argv):
  arena_ids = ids(BattleType.agent)
  print(arena_ids)
  for arena_id in arena_ids:
    arena_spec = spec(arena_id)
    print('id={}, type={}, kwargs={}'.format(arena_spec.id, arena_spec.type, arena_spec.def_kwargs))
    #env = make(env_id)
    #print(env)

if __name__ == '__main__':
  app.run(list_arena_spec)
