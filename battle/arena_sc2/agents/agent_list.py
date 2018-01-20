from battle.arena_sc2 import BattleType, make, ids, spec

import battle.arena_sc2.arenas
import battle.arena_sc2.envs
import battle.arena_sc2.agents

from absl import app

def list_agent_spec(unused_argv):
  agent_ids = ids(BattleType.agent)
  print(agent_ids)
  for agent_id in agent_ids:
    agent_spec = spec(agent_id)
    print('id={}, type={}, kwargs={}'.format(agent_spec.id, agent_spec.type, agent_spec.def_kwargs))
    #env = make(env_id)
    #print(env)

if __name__ == '__main__':
  app.run(list_agent_spec)
