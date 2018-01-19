# Game Arena Interface for sc2
class ArenaSC2():
    """
    Base Class for game arenas, defining the interface.
    """
    def __init__(self):
        raise NotImplementedError()

    def play_game(self):
        """Play the entire game"""
        raise NotImplementedError()

    def play_n(self, n):
        """Play n steps of the game

        :param n: number of time steps to play.
        """
        raise NotImplementedError()

    def play_episodes(self, episodes):
        """Play n episodes of the game

        :param episodes: number of episodes to play.
        """
        raise NotImplementedError()

    def register_agent(self, agents):
        """Register Agents

        :param agenta: an array of agent to register with the arena.
        """
        raise NotImplementedError()

    def register_env(self, envs):
        """ register environments of pysc2 to arena """
        raise NotImplementedError()

    def reset(self):
        """Reset the game to its start state."""
        raise NotImplementedError()

    def save_replay(self):
        raise NotImplementedError()
