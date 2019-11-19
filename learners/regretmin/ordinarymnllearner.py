"""
Learners under the  Multinomial Logit (MNL) bandit model.
"""

from abc import abstractmethod
from absl import logging

import numpy as np

from bandits import search_best_assortment
from .utils import RegretMinimizationLearner

__all__ = ['ExplorationExploitation']


class OrdinaryMNLLearner(RegretMinimizationLearner):
  """Base class for learners in the MNL bandit model"""

  @property
  @abstractmethod
  def name(self):
    pass

  @abstractmethod
  def _learner_init(self):
    pass

  @abstractmethod
  def choice(self, context):
    pass

  @abstractmethod
  def _learner_update(self, context, action, feedback):
    pass

  def __init__(self):
    super().__init__()

  def _model_init(self):
    if self._bandit.type != 'ordinarymnlbandit':
      logging.fatal(
          ("(ExplorationExploitation) I don't",
           " understand the bandit environment!"))

  def _model_update(self, context, action, feedback):
    pass


class ExplorationExploitation(OrdinaryMNLLearner):
  """Exploration-Exploitation algorithm for MNL-Bandit"""

  def __init__(self):
    super().__init__()
    self.__name = 'Exploration-Exploitation'

  def _learner_init(self):
    self.__prod_num = self._bandit.prod_num
    self.__revenue = self._bandit.context
    self.__K = self._bandit.card_constraint

    self.__ell = 1
    self.__v_ucb = np.ones(self.__prod_num)
    self.__purchases = np.zeros(self.__prod_num)
    self.__T = np.zeros(self.__prod_num)
    self.__update_epoch = False
    _, best_assort = search_best_assortment(self.__v_ucb,
        self.__revenue, self.__K)
    self.__s_ell = best_assort

  @property
  def name(self):
    return self.__name

  def choice(self, context):
    if self.__update_epoch:
      _, best_assort = search_best_assortment(self.__v_ucb,
          self.__revenue, self.__K)
      self.__s_ell = best_assort
    return self.__s_ell

  def _learner_update(self, context, action, feedback):
    """
    Input
      action: a list of product indexes
      feedback: (revenue, purchase observation)
    """

    self.__purchases[feedback[1]] += 1

    if feedback[1] == 0:
      for prod in self.__s_ell:
        self.__T[prod] += 1
      # calculate self._v_ucb
      bar_v = self.__purchases[self.__T!=0]/self.__T[self.__T!=0]
      tmp = 48*np.log(np.sqrt(self.__prod_num)*self.__ell+1) / \
          self.__T[self.__T!=0]
      self.__v_ucb[self.__T!=0] = bar_v + np.sqrt(bar_v*tmp) + tmp
      self.__v_ucb[self.__T==0] = 1
      self.__ell += 1
      self.__update_epoch = True