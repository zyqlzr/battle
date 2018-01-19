from battle.arena_sc2 import Agent
from pysc2.agents.base_agent import BaseAgent

class SC2WrapperAgent(Agent):
  """ agent wrapper, adapt the arena agent to pysc2 agent"""
  def __init__(self, sc2_agent):
    if not isinstance(sc2_agent, BaseAgent):
      raise Exception('input agent is not BaseAgent defined in pysc2')
    self.agent = sc2_agent

  def action(self, state):
    return self.agent.step(state)

  def get_sc2_agent(self):
    return self.agent

