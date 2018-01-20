from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from pysc2.lib import renderer_human
from pysc2 import maps
from pysc2 import run_configs
from s2clientprotocol import common_pb2 as sc_common
from s2clientprotocol import sc2api_pb2 as sc_pb

from battle.arena_sc2.envs.single_env import SingleEnv

class Battle1V1Env:
  def __init__(self,
               map_name=None,
               agent_races=None,
               screen_resolution=(64, 64),
               minimap_resolution=(64, 64),
               visualize=False, 
               **kwargs):
    self._map_name = map_name
    self._host_race = agent_races[0]
    self._client_race = agent_races[1]
    self._screen = screen_resolution
    self._minimap = minimap_resolution
    self._visualize = visualize
    self._kwargs = kwargs

  def setup_game(self):
    self._load_maps()
    self._launch_gamecores()
    self._create_game()
    self._join_game()
    game_controllers = [self._host, self._client]
    host = SingleEnv(run_config=self._run_config, 
                     controllers=game_controllers,
                     controller_pose=0,
                     **self._kwargs)

    client = SingleEnv(run_config=self._run_config, 
                       controllers=game_controllers,
                       controller_pose=1,
                       **self._kwargs)
    return (host, client,)

  def _load_maps(self):
    self._map = maps.get(self._map_name)
    print("MapInfo: [player_num={}, path_name={}]".format(
        self._map.players, 
        self._map.filename))
    if self._map.players != 2:
      raise Exception("the player number of map is err")

  def _launch_gamecores(self):
    agent_number = 2
    self._run_config = run_configs.get()
    procs = [self._run_config.start() for i in range(agent_number)]
    self._host = procs[0].controller
    self._client = procs[1].controller

  def _create_game(self):
    game = sc_pb.RequestCreateGame(local_map=sc_pb.LocalMap(
        map_path=self._map.path,
        map_data=self._run_config.map_data(self._map.path)))
    game.player_setup.add(type=sc_pb.Participant)
    game.player_setup.add(type=sc_pb.Participant)
    self._host.create_game(game)

  def _join_game(self):
    interface = sc_pb.InterfaceOptions(
        raw=self._visualize, score=True,
        feature_layer=sc_pb.SpatialCameraSetup(width=24))
    screen_size_px = point.Point(*self._screen)
    minimap_size_px = point.Point(*self._minimap)
    screen_size_px.assign_to(interface.feature_layer.resolution)
    minimap_size_px.assign_to(interface.feature_layer.minimap_resolution)

    hjoin = sc_pb.RequestJoinGame(race=races[self._host_race], options=interface)
    cjoin = sc_pb.RequestJoinGame(race=races[self._client_race], options=interface)
    self._host.join_game(hjoin)
    self._client.join_game(cjoin)
    return (self._host, self._client,)


