from battle.arena_sc2 import register, BattleType 

register(
  id='1V1Env',
  type=BattleType.env,
  entry_point='battle.arena_sc2.envs.multi_env:MultiEnv'
  map_name='Simple64',
  agent_races=['R', 'R'],
  screen_resolution=(64, 64),
  minimap_resolution=(64, 64),
  visualize=False,
  difficulty=None,
  step_mul=8,
  game_steps_per_episode=0,
)

