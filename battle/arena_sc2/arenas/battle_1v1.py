from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pysc2.lib import point
from pysc2.lib import renderer_human
from pysc2 import maps
from pysc2 import run_configs
from pysc2.env.sc2_env import races, difficulties
from pysc2.lib.remote_controller import RequestError

from s2clientprotocol import common_pb2 as sc_common
from s2clientprotocol import sc2api_pb2 as sc_pb

from battle.arena_sc2.envs.single_env import SingleEnv

from absl import logging
import time
import threading
import portpicker

GAME_NUM_1V1 = 2

HOST_CREATE = threading.Event()
CLIENT_JOIN = threading.Event()
HOST_JOIN = threading.Event()

class Battle1V1:
  def __init__(self,
               map_name=None,
               agent_races=None,
               screen_resolution=(64, 64),
               minimap_resolution=(64, 64),
               visualize=True,
               **kwargs):
    self._envs = None
    self._agents = None

    self._map_name = map_name
    self._host_race = agent_races[0]
    self._client_race = agent_races[1]
    self._screen = screen_resolution
    self._minimap = minimap_resolution
    self._visualize = visualize
    self._kwargs = kwargs
    self._controllers = None

  def play_game(self):
    pass

  def play_n(self, n):
    #self._play_asyncio(n)
    self._play_async(n)
    #self._play_sync(n)

  def play_episodes(self, episode_num):
    pass

  def register_agent(self, agents):
    if len(agents) != GAME_NUM_1V1:
      raise Exception('the number of input agents invalid')
    self._agents = agents 

  def register_env(self, envs):
    raise NotImplementedError

  def setup(self):
    pass

  def reset(self):
    """Reset the game to its start state."""
    pass

  def save_replay(self):
    pass

  def launch(self):
    return self._launch_gamecores()

  def env_controllers(self):
    return (e.controller for e in self._envs)

  def create_req(self, run_config):
    return self._create_pb(run_config)

  def host_join_req(self):
    return self._join_pb(self._host_race)

  def client_join_req(self):
    return self._join_pb(self._client_race)

  def score(self):
    return self._map.score_index

  def multi_score(self):
    return self._map.score_multiplier

  def episode_length(self):
    return self._map.game_steps_per_episode

  def _leave_games(self):
    if self._controllers is None:
      return

    for c in self._controllers:
      c.leave()

  def _exit_game_core(self):
    if self._controllers is None:
      return

    for c in self._controllers:
      c.quit()
    self._controllers = None

  def _setup_game(self):
    self._load_maps()
    host = SingleEnv(parent_env=self,
                     host=True,
                     score_index=self.score(),
                     score_multiplier=self.multi_score(),
                     game_steps_per_episode=self.episode_length(),
                     **self._kwargs)

    client = SingleEnv(parent_env=self,
                       host=False,
                       score_index=self.score(),
                       score_multiplier=self.multi_score(),
                       game_steps_per_episode=self.episode_length(),
                       **self._kwargs)
    self._envs = [host, client]

  def _load_maps(self):
    self._map = maps.get(self._map_name)
    print("MapInfo: [player_num={}, path_name={}]".format(
        self._map.players, 
        self._map.filename))
    if self._map.players != 2:
      raise Exception("the player number of map is err")

  def _launch_gamecores(self):
    run_config = run_configs.get()
    procs = run_config.start() 
    controller = procs.controller
    return (run_config, controller)

  def _create_pb(self, run_config):
    create = sc_pb.RequestCreateGame(local_map=sc_pb.LocalMap(
        map_path=self._map.path,
        map_data=run_config.map_data(self._map.path)))
    create.player_setup.add(type=sc_pb.Participant, race=races[self._host_race])
    create.player_setup.add(type=sc_pb.Participant, race=races[self._client_race])
    return create

  def pick_port(self):
    self._share_port = portpicker.pick_unused_port()
    self._svr_gport = portpicker.pick_unused_port()
    self._svr_bport = portpicker.pick_unused_port()
    self._c1_gport = portpicker.pick_unused_port()
    self._c1_bport = portpicker.pick_unused_port()
    self._c2_gport = portpicker.pick_unused_port()
    self._c2_bport = portpicker.pick_unused_port()
    print("share_port={}\n server_game_port={}\n server_base_port={}\n".format(
          self._share_port, self._svr_gport, self._svr_bport))
    print("client1_game_port={}\n client1_base_port={}\n".format(
          self._c1_gport, self._c1_bport))
    print("client2_game_port={}\n client2_base_port={}\n".format(
          self._c2_gport, self._c2_bport))

  def return_port(self):
    portpicker.return_port(self._share_port)
    portpicker.return_port(self._svr_gport)
    portpicker.return_port(self._svr_bport)
    portpicker.return_port(self._c1_gport)
    portpicker.return_port(self._c1_bport)
    portpicker.return_port(self._c2_gport)
    portpicker.return_port(self._c2_bport)

  def _join_pb(self, agent_race):
    interface = sc_pb.InterfaceOptions(
        raw=self._visualize, score=True)

    try:
      join = sc_pb.RequestJoinGame(race=races[agent_race],
                                    options=interface)
      join.shared_port = self._share_port
      join.server_ports.game_port = self._svr_gport
      join.server_ports.base_port = self._svr_bport
      hc1 = join.client_ports.add()
      hc1.game_port = self._c1_gport
      hc1.base_port = self._c1_bport
      hc2 = join.client_ports.add()
      hc2.game_port = self._c2_gport
      hc2.base_port = self._c2_bport
    except RequestError as e:
      print("res", e.res, ",exception:", e)
      raise Exception("setup game error")
    return join

  def _play_sync(self, n):
    print("**pick port**")
    self.pick_port()
    print("**setup port**")
    self._setup_game()
    if self._envs is None or self._agents is None:
      raise Exception('SC21V1 raise exception')
    self._setup_game_thread()
    self._controllers = (e.controller for e in self._envs)
    self._sync_step(n, False)
    print("**leave game**")
    self._leave_games()
    print("**exit game**")
    self._exit_game_core()
    print("**return port**")
    self.return_port()

  def _play_async(self, n):
    print("**pick port**")
    self.pick_port()
    print("**setup port**")
    self._setup_game()
    if self._envs is None or self._agents is None:
      raise Exception('SC21V1 raise exception')
    self._controllers = (e.controller for e in self._envs)
    self._run_game(n, False)
    print("**leave game**")
    self._leave_games()
    print("**exit game**")
    self._exit_game_core()
    print("**return port**")
    self.return_port()

  def _play_asyncio(self, n):
    print("**pick port**")
    self.pick_port()
    print("**setup port**")
    self._setup_game()
    if self._envs is None or self._agents is None:
      raise Exception('SC21V1 raise exception')
    self._controllers = (e.controller for e in self._envs)
    print('start run event loop')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
                               run_game_asyncio(0, self._agents[0], self._envs[0], n),
                               run_game_asyncio(1, self._agents[1], self._envs[1], n)))
    print('end run event loop')
    loop.close()
    print('close event loop')
    print("**leave game**")
    self._leave_games()
    print("**exit game**")
    self._exit_game_core()
    print("**return port**")
    self.return_port()

  def _run_game(self, max_step, save_replay):
    thread_count = 0
    threads = []
    print('env_num=', len(self._envs), 'agent_num=', len(self._agents))
    for agent, env in zip(self._agents, self._envs):
      env.set_uuid(thread_count)
      t = threading.Thread(target=Battle1V1.run_team_sequence, args=(thread_count, agent, env, max_step, save_replay))
      threads.append(t)
      t.start()
      thread_count += 1

    for t in threads:
      t.join()
    print('game over')

  @staticmethod
  def run_team(thread_id, agent, env, max_step, save_replay=False):
    print('thread-{} enter run_team'.format(thread_id))
    total_step = 0
    start_time = time.time()

    win = False
    try:
      """episode loop """
      print('setup game')
      env.reset_no_return()
      print('after reset and first step')
      timesteps = env.first_step()
      while True:
        total_step += 1
        print("--thread-{} step={}--".format(thread_id, total_step))
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
      print("thread-{} SC2_1V1 exception".format(thread_id))
    finally:
      end_time = time.time() - start_time
    print("thread-{} exit, game over, result={}".format(thread_id, win))
    if save_replay:
      env.save_replay()
    env.close()

  @staticmethod
  def run_team_sequence(thread_id, agent, env, max_step, save_replay=False):
    print('thread-{} enter run_team_sequence'.format(thread_id))
    total_step = 0
    start_time = time.time()

    win = False
    try:
      """episode loop """
      print('setup game by run_team_sequence')
      env.reset_launch()
      if env.host:
        print('host create game, thread-{}'.format(thread_id))
        HOST_CREATE.set()
        HOST_JOIN.set()
        env.reset_join()
        print('host wait for client join, thread-{}'.format(thread_id))
        CLIENT_JOIN.wait()
        print('host and client all join, thread-{}'.format(thread_id))
      else:
        HOST_CREATE.wait()
        print('client know the game create, thread-{}'.format(thread_id))
        CLIENT_JOIN.set()
        env.reset_join()
        print('client wait for host create, thread-{}'.format(thread_id))
        HOST_JOIN.wait()
        print('client and host all join, thread-{}'.format(thread_id))
      print('after reset and first step, thread-{}'.format(thread_id))
      #SEMAPHORE.acquire()
      timesteps = env.first_step()
      #actions = [agent.step(timestep) for timestep in timesteps]
      #timesteps = env.step(actions)
      print('end reset and first step, thread-{}'.format(thread_id))
      #SEMAPHORE.release()
      if env.host:
        print('host finish first action,thread-{}'.format(thread_id))
      else:
        print('client finish first action,thread-{}'.format(thread_id))

      while True:
        total_step += 1
        print("--thread-{} step={}--".format(thread_id, total_step))
        #SEMAPHORE.acquire()
        actions = [agent.step(timestep) for timestep in timesteps]
        timesteps = env.step_test(actions)
        #SEMAPHORE.release()

        if max_step and total_step >= max_step:
          break

        '''
        if timesteps[0].last():
          total_episode += 1
          if timesteps[0].reward > 0:
            win = True
          else:
            None
          break
        '''
    except KeyboardInterrupt:
      print("thread-{} SC2_1V1 exception".format(thread_id))
    finally:
      end_time = time.time() - start_time
    print("thread-{} exit, game over, result={}".format(thread_id, win))
    if save_replay:
      env.save_replay()
    env.close()


  def _setup_game_thread(self):
    thread_count = 0
    threads = []
    print('env_num=', len(self._envs))
    for env in self._envs:
      env.set_uuid(thread_count)
      t = threading.Thread(target=Battle1V1.setup_multi_agent_game, args=([env]))
      threads.append(t)
      t.start()
      thread_count += 1

    for t in threads:
      t.join()
    print('setup game finished')

  def _sync_step(self, max_step, save_replay):
    henv = self._envs[0]
    hagent = self._agents[0]
    cenv = self._envs[1]
    cagent = self._agents[1]

    hts =  henv.first_step()
    hts = self._exec_step(henv, hagent, hts)

    cts = cenv.first_step()
    cts = self._exec_step(cenv, cagent, cts)

    for _ in range(max_step):
      hts = self._exec_step(henv, hagent, hts)
      cts = self._exec_step(cenv, cagent, cts)
      if hts[0].last() or cts[0].last():
          print("execute end")
          break
      if hts is None or cts is None:
          print("execute error")
          break
    print("sync step end")

  def _exec_step(self, env, agent, last_timesteps):
    try:
        actions = [agent.step(timestep) for timestep in last_timesteps]
        timesteps = env.step(actions)
        return timesteps
    except KeyboardInterrupt:
      print("execute step failed")
    return None

  @staticmethod
  def setup_multi_agent_game(env):
    env.reset_no_return()

