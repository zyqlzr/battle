from battle.arena_sc2 import BattleType, make, ids, spec

import battle.arena_sc2.arenas
import battle.arena_sc2.envs
import battle.arena_sc2.agents

from absl import app

def list_env_spec(unused_argv):
  env_ids = ids(BattleType.env)
  print(env_ids)
  for env_id in env_ids:
    env_spec = spec(env_id)
    print('id={}, type={}, kwargs={}'.format(
        env_spec.id, 
        env_spec.type, 
        env_spec.def_kwargs))
    #env = make(env_id)
    #print(env)

if __name__ == '__main__':
  app.run(list_env_spec)
