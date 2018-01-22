from battle.arena_sc2 import SC2WrapperAgent, make, ids

import battle.arena_sc2.arenas
import battle.arena_sc2.agents
import battle.arena_sc2.envs

from absl import flags
from absl import app
import time


def run_agent_vs_agent(unused_argv):
  print("all register id=", ids())
  agents = [make('NoopAgent') for _ in range(2)]

  sc2_battle = make('Battle1V1')
  print("**register agent**")
  sc2_battle.register_agent(agents)
  print("**register env**")
  print("**play game**")
  sc2_battle.play_n(500)
  time.sleep(20)

if __name__ == '__main__':
  app.run(run_agent_vs_agent)

