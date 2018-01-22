from battle.arena_sc2 import register, BattleType

register(
  id='AgentVSBuiltIn',
  type=BattleType.arena,
  entry_point='battle.arena_sc2.arenas.sc2_builtin:SC2AgentVSBuildIn',
)

register(
  id='Agent1V1',
  type=BattleType.arena,
  entry_point='battle.arena_sc2.arenas.sc2_1v1:SC21V1',
)

register(
  id='Battle1V1',
  type=BattleType.arena,
  entry_point='battle.arena_sc2.arenas.battle_1v1:Battle1V1',
  map_name='Simple64',
  agent_races=['R', 'R'],
  screen_resolution=(64, 64),
  minimap_resolution=(64, 64),
  visualize=True,
  step_mul=8,
)

