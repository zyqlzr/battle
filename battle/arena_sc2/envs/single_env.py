# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A Starcraft II environment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import logging

from pysc2 import maps
from pysc2 import run_configs
from pysc2.env import environment
from pysc2.lib import features
from pysc2.lib import point
from pysc2.lib import renderer_human
from pysc2.lib import stopwatch
from pysc2.env.sc2_env import races, difficulties, _possible_results

from s2clientprotocol import common_pb2 as sc_common
from s2clientprotocol import sc2api_pb2 as sc_pb
sw = stopwatch.sw

class SingleEnv(environment.Base):
  """A Starcraft II environment.
  The implementation details of the action and observation specs are in
  lib/features.py
  """

  def __init__(self,
               parent_env=None,
               host=False,
               **kwargs):
    # pylint: disable=g-doc-args
    # pylint: enable=g-doc-args
    self._action_pb = False
    self._host = host
    self._parent = parent_env
    print("parent_env=", parent_env, "type=", type(parent_env))
    self._setup(**kwargs)
    self._uid = -1

  def _setup(self,
             discount=1.,
             visualize=False,
             step_mul=None,
             save_replay_episodes=0,
             replay_dir=None,
             game_steps_per_episode=None,
             score_index=None,
             score_multiplier=None):
    if save_replay_episodes and not replay_dir:
      raise ValueError("Missing replay_dir")

    self._discount = discount
    self._step_mul = step_mul or self._map.step_mul
    self._save_replay_episodes = save_replay_episodes
    self._replay_dir = replay_dir
    self._total_steps = 0

    self._score_index = score_index
    self._score_multiplier = score_multiplier
    self._last_score = None

    self._episode_length = game_steps_per_episode
    self._episode_steps = 0
    self._visualize = visualize

  def set_uuid(self, uid):
    self._uid = uid

  @sw.decorate
  def reset(self):
    print('---SingleEnv reset---, host=', self._host)
    self._run_config, self._controller= self._parent.launch()
    if self._host:
      create = self._parent.create_req(self._run_config)
      print("--create_pb--, uuid=", self._uid)
      self.controller.create_game(create)
      print('--host join multi-player game--, uuid=', self._uid)
      hjrsp = self.controller.join_game(self._parent.host_join_req())
      print('--host join response:--, uuid=', self._uid)
    else:
      print('--client join multi-player game--, uuid=', self._uid)
      cjrsp = self.controller.join_game(self._parent.client_join_req())
      print('--client join response:--, uuid=', self._uid)

    self._controllers = self._parent.env_controllers()
    self._num_players = 2
    self._game_info = self.controller.game_info()
    self._obs = None
    self._state = environment.StepType.LAST  # Want to jump to `reset`.
    self.feature()
    self.renderer()

    self._last_score = [0] * 2
    self._state = environment.StepType.FIRST
    return self._step()

  def feature(self):
    self._features = features.Features(self._game_info)

  def renderer(self):
    print('renderer, visualize=', self._visualize)
    if self._visualize:
      static_data = self.controller.data()
      self._renderer_human = renderer_human.RendererHuman()
      self._renderer_human.init(self._game_info, static_data)
    else:
      self._renderer_human = None

  def observation_spec(self):
    """Look at Features for full specs."""
    return self._features.observation_spec()

  def action_spec(self):
    """Look at Features for full specs."""
    return self._features.action_spec()

  def step_renderer(self, obs):
    if self._renderer_human:
      self._renderer_human.render(obs)
      cmd = self._renderer_human.get_actions(
          self._run_config, self.controller)
      if cmd == renderer_human.ActionCmd.STEP:
        pass
      elif cmd == renderer_human.ActionCmd.RESTART:
        self._state = environment.StepType.LAST
      elif cmd == renderer_human.ActionCmd.QUIT:
        raise KeyboardInterrupt("Quit?")

  def step_action(self, actions):
    '''
    controller_count = 0
    for c in self._controllers:
      print('controller-{} act'.format(controller_count))
      [c.act(self._features.transform_action(o.observation, a, True))
          for o, a in zip(self._obs, actions)]
      controller_count += 1
    '''
    print('----step action----, uuid=', self._uid)
    #self.controller.step(self._step_mul)
    [self.controller.act(self._features.transform_action(o.observation, a, True))
        for o, a in zip(self._obs, actions)]
    print('----step recv action rsp----, uuid=', self._uid)

  def step_obs(self):
    #for c in self._controllers:
    #  c.step(self._step_mul)
    print('----step obs----, uuid=', self._uid)
    self._obs = [self.controller.observe()]
    self.controller.step(self._step_mul)
    print('----step recv obs rsp----, uuid=', self._uid)
    agent_obs = [self._features.transform_obs(o.observation) for o in self._obs]
    return agent_obs

  @sw.decorate
  def step(self, actions):
    """Apply actions, step the world forward, and return observations."""
    #if self._state == environment.StepType.LAST:
    #  return self.reset()
    print('SingleEnv step, uuid=', self._uid)
    #self.step_action(actions)
    self._state = environment.StepType.MID
    return self._step()

  def _step(self):
    agent_obs = self.step_obs()
    # TODO(tewalds): How should we handle more than 2 agents and the case where
    # the episode can end early for some agents?
    outcome = [0] * self._num_players
    discount = self._discount
    if any(o.player_result for o in self._obs):  # Episode over.
      self._state = environment.StepType.LAST
      discount = 0
      for i, o in enumerate(self._obs):
        player_id = o.observation.player_common.player_id
        for result in o.player_result:
          if result.player_id == player_id:
            outcome[i] = _possible_results.get(result.result, 0)

    if self._score_index >= 0:  # Game score, not win/loss reward.
      cur_score = [o["score_cumulative"][self._score_index] for o in agent_obs]
      if self._episode_steps == 0:  # First reward is always 0.
        reward = [0] * self._num_players
      else:
        reward = [cur - last for cur, last in zip(cur_score, self._last_score)]
      self._last_score = cur_score
    else:
      reward = outcome

    #renderer
    #self.step_renderer(self._obs[0])

    self._total_steps += self._step_mul
    self._episode_steps += self._step_mul
    if self._episode_length > 0 and self._episode_steps >= self._episode_length:
      self._state = environment.StepType.LAST
      # No change to reward or discount since it's not actually terminal.

    if self._state == environment.StepType.LAST:
      logging.info(
          "Episode finished. Outcome: %s, reward: %s, score: %s",
          outcome, reward, [o["score_cumulative"][0] for o in agent_obs])

    return tuple(environment.TimeStep(step_type=self._state,
                                      reward=r * self._score_multiplier,
                                      discount=discount, observation=o)
                 for r, o in zip(reward, agent_obs))

  def save_replay(self, replay_dir):
    replay_path = self._run_config.save_replay(
        self._controllers[0].save_replay(), replay_dir, self._map.name)
    logging.info("Wrote replay to: %s", replay_path)

  @property
  def state(self):
    return self._state

  def close(self):
    logging.info("Environment Close")
    if hasattr(self, "_renderer_human") and self._renderer_human:
      self._renderer_human.close()
      self._renderer_human = None

    # Don't use parallel since it might be broken by an exception.
    '''
    if hasattr(self, "_controller") and self._controller:
      self.controller.leave()
      #self.controller.quit()
    if hasattr(self, "_sc2_proc") and self._sc2_proc:
      for p in self._sc2_procs:
        p.close()
      self._sc2_procs = None
    '''

  def action_raw_flag(self):
    self._action_pb = True

  def action_sc2_flag(self):
    self._action_pb = False

  @property
  def obs_pb(self):
    return self._obs

  @property
  def controller(self):
    return self._controller

  def reset_no_return(self):
    print('---SingleEnv reset---, host=', self._host)
    self._run_config, self._controller= self._parent.launch()
    if self._host:
      create = self._parent.create_req(self._run_config)
      print("--create_pb--, uuid=", self._uid)
      self.controller.create_game(create)
      print('--host join multi-player game--, uuid=', self._uid)
      hjrsp = self.controller.join_game(self._parent.host_join_req())
      print('--host join response:--, uuid=', self._uid)
    else:
      print('--client join multi-player game--, uuid=', self._uid)
      cjrsp = self.controller.join_game(self._parent.client_join_req())
      print('--client join response:--, uuid=', self._uid)

    self._controllers = self._parent.env_controllers()
    self._num_players = 2
    self._game_info = self.controller.game_info()
    self._obs = None
    self._state = environment.StepType.LAST  # Want to jump to `reset`.
    self.feature()
    self.renderer()

    self._last_score = [0] * 2
    self._state = environment.StepType.FIRST


  @property
  def host(self):
    return self._host

  def reset_launch(self):
    print('---SingleEnv reset---, host=', self._host)
    self._run_config, self._controller= self._parent.launch()
    if self._host:
      create = self._parent.create_req(self._run_config)
      print("--create_pb--, uuid=", self._uid)
      self.controller.create_game(create)

  def reset_join(self):
    if self._host:
      print('--host join multi-player game--, uuid=', self._uid)
      hjrsp = self.controller.join_game(self._parent.host_join_req())
      print('--host join response:--, uuid=', self._uid)
    else:
      print('--client join multi-player game--, uuid=', self._uid)
      cjrsp = self.controller.join_game(self._parent.client_join_req())
      print('--client join response:--, uuid=', self._uid)

    self._controllers = self._parent.env_controllers()
    self._num_players = 2
    self._game_info = self.controller.game_info()
    print("get game_info, uuid=", self._uid)
    self._obs = None
    self._state = environment.StepType.LAST  # Want to jump to `reset`.
    #self.feature()
    #self.renderer()

    self._last_score = [0] * 2
    self._state = environment.StepType.FIRST

  def step_action_test(self, actions):
    '''
    controller_count = 0
    for c in self._controllers:
      print('controller-{} act'.format(controller_count))
      [c.act(self._features.transform_action(o.observation, a, True))
          for o, a in zip(self._obs, actions)]
      controller_count += 1
    '''
    print('----step_test action----, uuid=', self._uid)
    #self.controller.step(self._step_mul)
    [self.controller.act(self._features.transform_action(o.observation, a, True))
        for o, a in zip(self._obs, actions)]
    print('----step_test recv action rsp----, uuid=', self._uid)

  def step_obs_test(self):
    #for c in self._controllers:
    #  c.step(self._step_mul)
    print('----step_test obs----, uuid=', self._uid)
    self._obs = [self.controller.observe()]
    self.controller.step(self._step_mul)
    print('----step_test recv obs rsp----, uuid=', self._uid)
    #agent_obs = [self._features.transform_obs(o.observation) for o in self._obs]
    #return agent_obs

  @sw.decorate
  def first_step(self):
    self.step_obs_test()
    return tuple(environment.TimeStep(step_type=self._state,
                                      reward=0,
                                      discount=0, observation=None))

  @sw.decorate
  def step_test(self, actions):
    self._state = environment.StepType.MID
    #self.step_action_test(actions)
    self.step_obs_test()
    return tuple(environment.TimeStep(step_type=self._state,
                                      reward=0,
                                      discount=0, observation=None))

