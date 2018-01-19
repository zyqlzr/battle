# Game / Training Environment Framework

class Agent():
  """
  Interface required for Agents that can play in the arena.
  """
  def setup(self, model_path=None):
    raise NotImplementedError()

  def reset(self, model_path=None):
    raise NotImplementedError()

  def step(self, obs):
    """Given a frame state, output an action predicted by the AI for this agent.

    :param state: a game state
    :returns: an action allowed in the current game
    """
    raise NotImplementedError()

