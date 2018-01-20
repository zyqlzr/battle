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

