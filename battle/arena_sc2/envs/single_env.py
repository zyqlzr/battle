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
from pysc2.lib import run_parallel
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

  def __init__(self,  # pylint: disable=invalid-name
               run_config=None,
               controllers=None,
               controller_pose=None,
               **kwargs):
    # pylint: disable=g-doc-args
    # pylint: enable=g-doc-args
    self._setup(**kwargs)
    self._action_pb = False
    self._controllers = controllers
    self._cpose = controller_pose
    self._run_config = run_config

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

    if score_index is None:
      self._score_index = self._map.score_index
    else:
      self._score_index = score_index
    if score_multiplier is None:
      self._score_multiplier = self._map.score_multiplier
    else:
      self._score_multiplier = score_multiplier
    self._last_score = None

    self._episode_length = (game_steps_per_episode or
                            self._map.game_steps_per_episode)
    self._episode_steps = 0

    self._parallel = run_parallel.RunParallel()  # Needed for multiplayer.
    self._features = features.Features(game_info)
    self._episode_count = 0
    self._obs = None
    self._state = environment.StepType.LAST  # Want to jump to `reset`.
    self.renderer(visualize)
    logging.info("Environment is ready.")

  def renderer(self, visualize):
    if visualize:
      game_info = self._controllers[self._cpose].game_info()
      static_data = self._controllers[self._cpose].data()
      self._renderer_human = renderer_human.RendererHuman()
      self._renderer_human.init(game_info, static_data)
    else:
      self._renderer_human = None

  def observation_spec(self):
    """Look at Features for full specs."""
    return self._features.observation_spec()

  def action_spec(self):
    """Look at Features for full specs."""
    return self._features.action_spec()

  def _restart(self):
    self._controllers[self._cpose].restart()

  @sw.decorate
  def reset(self):
    """Start a new episode."""
    self._episode_steps = 0
    if self._episode_count:
      # No need to restart for the first episode.
      self._restart()

    self._episode_count += 1
    logging.info("Starting episode: %s", self._episode_count)

    self._last_score = [0] * self._num_players
    self._state = environment.StepType.FIRST
    return self._step()

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
    print("action_flag=", self._action_pb)
    if self._action_pb:
      [self.controller.act(a) for a in actions]
    else:
      for c in self._controllers:
        [c.act(self._features.transform_action(o.observation, a, True))
            for o, a in zip(self._obs, actions)]

  def step_obs(self):
    self.controller.step(self._step_mul)
    self._obs = self.controller.observe()
    agent_obs = [self._features.transform_obs(o.observation) for o in self._obs]
    return agent_obs

  @sw.decorate
  def step(self, actions):
    """Apply actions, step the world forward, and return observations."""
    if self._state == environment.StepType.LAST:
      return self.reset()

    self.step_action(actions)
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
    self.step_renderer(self._obs[0])

    self._total_steps += self._step_mul
    self._episode_steps += self._step_mul
    if self._episode_length > 0 and self._episode_steps >= self._episode_length:
      self._state = environment.StepType.LAST
      # No change to reward or discount since it's not actually terminal.

    if self._state == environment.StepType.LAST:
      if (self._save_replay_episodes > 0 and
          self._episode_count % self._save_replay_episodes == 0):
        self.save_replay(self._replay_dir)
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
    if hasattr(self, "_controller") and self._controller:
      for c in self._controllers:
        c.quit()
      self._controllers = None
    if hasattr(self, "_sc2_proc") and self._sc2_proc:
      for p in self._sc2_procs:
        p.close()
      self._sc2_procs = None

    logging.info(sw)

  def action_raw_flag(self):
    self._action_pb = True

  def action_sc2_flag(self):
    self._action_pb = False

  @property
  def obs_pb(self):
    return self._obs

  @property
  def controller(self):
    return self._controllers[self._cpose]

