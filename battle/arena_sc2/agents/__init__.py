from battle.arena_sc2 import register, BattleType

register(
  id='RandomAgent',
  type=BattleType.agent,
  entry_point='pysc2.agents.random_agent:RandomAgent'
)

