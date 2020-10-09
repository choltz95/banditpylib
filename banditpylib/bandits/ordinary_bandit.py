from typing import List, Tuple

import numpy as np

from banditpylib.arms import Arm
from banditpylib.learners import Goal, BestArmId, MaxReward
from .ordinary_bandit_itf import OrdinaryBanditItf


class OrdinaryBandit(OrdinaryBanditItf):
  r"""Ordinary bandit

  Arms are indexed from 0 by default. Each pull of arm :math:`i` will generate
  an `i.i.d.` reward from distribution :math:`\mathcal{D}_i`, which is unknown
  beforehand.
  """

  def __init__(self, arms: List[Arm], name: str = None):
    """
    Args:
      arms: arms in ordinary bandit
      name: alias name
    """
    super().__init__(name)
    if len(arms) < 2:
      raise Exception('The number of arms %d is less than 2!' % len(arms))
    self.__arms = arms
    self.__arm_num = len(arms)
    # find the best arm
    self.__best_arm_id = max(
        [(arm_id, arm.mean) for (arm_id, arm) in enumerate(self.__arms)],
        key=lambda x: x[1])[0]
    self.__best_arm = self.__arms[self.__best_arm_id]

  def _name(self) -> str:
    """
    Returns:
      default bandit name
    """
    return 'ordinary_bandit'

  def _take_action(self, arm_id: int, pulls: int = 1) -> \
      Tuple[np.ndarray, None]:
    """Pull one arm

    Args:
      arm_id: arm to pull
      pulls: number of times to pull

    Returns:
      feedback after `arm_id` is pulled where the first dimention is the
        stochstic rewards
    """
    if arm_id not in range(self.__arm_num):
      raise Exception('Arm id %d is out of range [0, %d)!' % \
          (arm_id, self.__arm_num))
    # empirical rewards when `arm_id` is pulled for `pulls` times
    em_rewards = self.__arms[arm_id].pull(pulls)
    if em_rewards is not None:
      self.__regret += (self.__best_arm.mean * pulls - sum(em_rewards))
      self.__total_pulls += pulls
    return (em_rewards, None)

  def feed(self, actions: List[Tuple[int, int]]) -> \
      List[Tuple[np.ndarray, None]]:
    """Pull multiple arms

    Args:
      actions: for each tuple, the first dimension denotes the arm id and the
        second dimension is the number of times to pull

    Returns:
      feedback after arms are pulled. For each tuple, the first dimention is
        the stochstic rewards.
    """
    feedback = []
    for (arm_id, pulls) in actions:
      feedback.append(self._take_action(arm_id, pulls))
    return feedback

  def reset(self):
    """Reset the bandit environment

    .. warning::
      This function should be called before the start of the game.
    """
    self.__total_pulls = 0
    self.__regret = 0.0

  def arm_num(self) -> int:
    """
    Returns:
      total number of arms
    """
    return self.__arm_num

  def total_pulls(self) -> int:
    """
    Returns:
      total number of pulls
    """
    return self.__total_pulls

  def __best_arm_regret(self, arm_id: int) -> int:
    """
    Args:
      arm_id: best arm identified by the learner

    Returns:
      regret compared with the best arm
    """
    return int(self.__best_arm_id != arm_id)

  def regret(self, goal: Goal) -> float:
    """
    Args:
      goal: goal of the learner

    Returns:
      regret of the learner
    """
    if isinstance(goal, BestArmId):
      return self.__best_arm_regret(goal.value)
    elif isinstance(goal, MaxReward):
      return self.__regret
    raise Exception('Goal %s is not supported!' % goal.name)
