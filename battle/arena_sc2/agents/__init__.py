from battle.arena_sc2 import register, BattleType

register(
  id='RandomAgent',
  type=BattleType.agent,
  entry_point='pysc2.agents.random_agent:RandomAgent'
)

register(
  id='NoopAgent',
  type=BattleType.agent,
  entry_point='battle.arena_sc2.agents.noop_agent:NoopAgent',
)

