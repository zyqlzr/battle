from battle.arena_sc2 import Agent, ArenaSC2

from absl import logging
import time
import threading

GAME_NUM_1V1 = 2
Mutex = threading.Lock() 

""" only support agent vs built-in"""
class SC21V1(ArenaSC2):
  def __init__(self):
    self._envs = None
    self._agents = None

  def play_game(self):
    pass

  def play_n(self, n):
    if self._envs is None or self._agents is None:
      raise Exception('SC21V1 raise exception')
    self._run_game(n, False)

  def play_episodes(self, episode_num):
    pass

  def register_agent(self, agents):
    if len(agents) != GAME_NUM_1V1:
      raise Exception('the number of input agents invalid')
    self._agents = agents 

  def register_env(self, envs):
    if len(envs) != GAME_NUM_1V1:
      raise Exception('the number of input envs invalid')
    self._envs = envs

  def setup(self):
    pass

  def reset(self):
    """Reset the game to its start state."""
    pass

  def save_replay(self):
    pass

  def _run_game(self, max_step, save_replay):
    threads = [threading.Thread(target=SC21V1.run_team, args=(agent, env, max_step, save_replay))
               for agent, env in zip(self._agents, self._envs)]
    for t in threads:
      t.start()

    for t in threads:
      t.join()
    print('game over')  

  @staticmethod
  def run_team(agent, env, max_step, save_replay=False):
    total_step = 0
    start_time = time.time()

    win = False
    try:
      """episode loop """
      timesteps = self.reset()
      while True:
        total_step += 1
        actions = [agent.step(timestep) for timestep in timesteps]
        timesteps = env.step(actions)

        if max_step and total_step >= max_step:
          break

        if timesteps[0].last():
          total_episode += 1
          if timesteps[0].reward > 0:
            win = True
          else:
            None
          break
    except KeyboardInterrupt:
      print("SC2_1V1 exception")
    finally:
      end_time = time.time() - start_time
    print("game over, result={}".format(win))
    if save_replay:
      env.save_replay()

