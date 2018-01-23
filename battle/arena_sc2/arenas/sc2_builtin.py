from battle.arena_sc2 import Agent, ArenaSC2

from absl import logging
import time

class RunStatistic:
  def __init__(self):
    self.total_steps = 0
    self.total_time = 0
    self.total_episode = 0
    self.win_count = 0
    self.lose_count = 0

  def __str__(self):
    return "step:%s times:%s episode:%s win:%s lost:%s" % (
        self.total_step, self.total_time, 
        self.total_episode, self.win_count, self.lose_count)

""" only support agent vs built-in"""
class SC2AgentVSBuildIn(ArenaSC2):
  def __init__(self):
    self._env = None
    self._agent = None
    self._stat = RunStatistic()
    self._replay_dir = "."

  def play_game(self):
    if self._env is None or self._agent is None:
      logging.error("env or agent is None") 
      return

    self._inner_run([self._agent], self._env, None, 1)

  def play_n(self, n):
    if self._env is None or self._agent is None:
      logging.error("env or agent is None") 
      return

    self._inner_run([self._agent], self._env, n, 1)

  def play_episodes(self, episode_num):
    if self._env is None or self._agent is None:
      logging.error("env or agent is None") 
      return

    self._inner_run([self._agent], self._env, None, episode_num)

  def register_agent(self, new_agent):
    if self._agent is None:
      self._agent = new_agent.get_sc2_agent()
    else:
      logging.error("repeat register agent")

  def register_env(self, env):
    if self._env is None:
      self._env = env
    else:
      logging.error("repeat register env")

  def setup(self):
    self._agent.setup(self._env.observation_spec(), self._env.action_spec())

  def reset(self):
    """Reset the game to its start state."""
    timesteps = self._env.reset()
    self._agent.reset()
    return timesteps

  def save_replay(self):
    self._env.save_replay(self._replay_dir)

  def _inner_run(self, agents, env, max_step, max_episode):
    total_step = 0
    total_episode = 0
    start_time = time.time()          
    self.setup()
    end = False

    try:
      """episode loop """
      while True:
        timesteps = self.reset()
        print("step_len=", len(timesteps), "agent_len=", len(agents))
        while True:
          total_step += 1
          actions = [agent.step(timestep) for agent, timestep in zip(agents, timesteps)]
          timesteps = env.step(actions)

          if max_step and total_step >= max_step:
            end = True
            total_episode += 1
            self.save_replay()
            break

          if timesteps[0].last():
            total_episode += 1
            if timesteps[0].reward > 0:
                self._stat.win_count += 1
            elif timesteps[0].reward < 0:
                self._stat.lose_count += 1
            else:
                None
            self.save_replay()
            break
          #print("step=", total_step)

        if max_episode and total_episode >= max_episode:
          break 

        if end is True:
          break
    except KeyboardInterrupt:
      print("SC2Imp exception")
    finally:
      end_time = time.time() - start_time
      self._stat.total_step = total_step
      self._stat.total_episode = total_episode
      self._stat.total_time = end_time

  @property
  def stat(self):
    return self._stat

