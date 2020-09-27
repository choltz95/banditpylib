from typing import List, Dict

import numpy as np

from banditpylib.bandits import Bandit
from banditpylib.learners import Learner
from .utils import Protocol


class SinglePlayerProtocol(Protocol):
  """Single player protocol

  This protocol is used to simulate the ordinary single-player game.
  """
  def __init__(self,
               bandit: Bandit,
               learners: List[Learner],
               intermediate_regrets: List[int] = None):
    """
    Args:
      bandit: bandit environment
      learner: learners to be compared with
      intermediate_regrets: a list of intermediate times to record
        intermediate regrets
    """
    super().__init__(bandit=bandit, learners=learners)
    self.__intermediate_regrets = \
        intermediate_regrets if intermediate_regrets is not None else []

  @property
  def name(self):
    """protocol name"""
    return 'single_player_protocol'

  def _one_trial(self, random_seed: int) -> List[Dict]:
    """One trial of the game

    Args:
      random_seed: random seed

    Returns:
      result of one trial
    """
    np.random.seed(random_seed)

    # reset the bandit environment and the learner
    self.bandit.reset()
    self.current_learner.reset()

    one_trial_data = []
    # number of rounds to communicate with the bandit environment
    adaptive_rounds = 0
    # total actions executed by the bandit environment
    total_actions = 0

    def record_data():
      one_trial_data.append(
          dict({
              'bandit': self.bandit.name,
              'learner': self.current_learner.name,
              'rounds': adaptive_rounds,
              'total_actions': total_actions,
              'regret': self.current_learner.regret(self.bandit)
          }))

    while True:
      context = self.bandit.context()
      actions = self.current_learner.actions(context)

      # stop the game if actions returned by the learner are None
      if actions is None:
        break

      # record intermediate regrets
      if adaptive_rounds in self.__intermediate_regrets:
        record_data()

      feedback = self.bandit.feed(actions)
      self.current_learner.update(feedback)

      # information update
      for (_, times) in actions:
        total_actions += int(times)
      adaptive_rounds += 1

    # record final regret
    record_data()
    return one_trial_data
