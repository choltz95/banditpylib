from importlib import import_module

from abc import abstractmethod
from absl import logging
import numpy as np

from .ordinarybandit import OrdinaryBanditItf
from .utils import Bandit

__all__ = ['LinearBanditItf', 'LinearBandit']

ARM_PKG = 'banditpylib.bandits.arms'


class LinearBanditItf(Bandit):
  """linear bandit interface"""

  @property
  @abstractmethod
  def arm_num(self):
    pass

  @property
  @abstractmethod
  def tot_samples(self):
    pass

  @property
  @abstractmethod
  def features(self):
    pass


class LinearBandit(
    OrdinaryBanditItf,
    LinearBanditItf):
  """correlated bandit
  Arms are numbered from 0 to len(arms)-1 by default.
  """

  def __init__(self, pars):
    features = pars['features']
    if len(features) < 2:
      logging.fatal('The number of arms should be at least two!')
    if not isinstance(features, list):
      logging.fatal('Features should be given in a list!')
    self.__features = [np.array(feature) for feature in features]
    self.__theta = np.array(pars['theta'])
    for _, feature in enumerate(self.__features):
      if feature.shape != self.__theta.shape:
        logging.fatal('The feature and theta dimensions are unequal!')
    Arm = getattr(import_module(ARM_PKG), 'GaussianArm')
    if 'var' not in pars:
      logging.warn('%s: variance of noise is assumed to be 1!' % self.type)
      self.__var = 1
    else:
      self.__var = pars['var']
    arms = [Arm(np.dot(feature, self.__theta),
                self.__var) for feature in self.__features]
    self.__arms = arms
    self.__arm_num = len(arms)
    self.__best_arm_ind = max(
        [(tup[0], tup[1].mean) for tup in enumerate(self.__arms)],
        key=lambda x: x[1])[0]
    self.__best_arm = self.__arms[self.__best_arm_ind]

  @property
  def arm_num(self):
    """return number of arms"""
    return self.__arm_num

  @property
  def arm_type(self):
    return 'GaussianArm'

  @property
  def type(self):
    return 'linearbandit'

  @property
  def tot_samples(self):
    return self.__tot_samples

  def init(self):
    self.__tot_samples = 0
    self.__max_rewards = 0

  @property
  def context(self):
    return None

  @property
  def features(self):
    return self.__features

  def _take_action(self, action):
    is_list = True
    if not isinstance(action, list):
      is_list = False
      action = [(action, 1)]

    rewards = []
    for tup in action:
      ind = tup[0]
      if ind not in range(self.__arm_num):
        logging.fatal('Wrong arm index!')
      rewards.append(self.__arms[ind].pull(tup[1]))
      self.__tot_samples += tup[1]
      self.__max_rewards += (self.__best_arm.mean * tup[1])

    if not is_list:
      # rewards[0] is a numpy array with size 1
      return (rewards[0][0],)
    return (rewards,)

  def _update_context(self):
    pass

  def __regret(self, rewards):
    return self.__max_rewards - rewards

  def __best_arm_regret(self, ind):
    return 1 - (self.__best_arm_ind == ind)
