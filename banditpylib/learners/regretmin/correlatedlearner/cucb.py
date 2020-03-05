from absl import logging

import numpy as np
import cvxpy as cp

from .utils import CorrelatedLearner

__all__ = ['CUCB']


class CUCB(CorrelatedLearner):
  """CUCB"""

  def __init__(self, pars):
    super().__init__(pars)
    self._name = self._name if self._name else 'CUCB'
    self.__alpha = float(pars['alpha']) if 'alpha' in pars else 2
    if self.__alpha <= 0:
      logging.fatal('%s: alpha should be greater than 0!' % self._name)

  def _learner_init(self):
    pass

  def learner_choice(self, context):
    """return an arm to pull"""
    if self._t <= self._arm_num:
      return (self._t-1) % self._arm_num

    em_comp = list(range(self._arm_num)) # arm index
    # index of most pulled arm
    k_max = np.argmax([arm.pulls for arm in self._em_arms])
    arm_kmax = self._em_arms[k_max]
    n_kmax = arm_kmax.pulls # number pulls for  most pulled arm
    mu_kmax = arm_kmax.em_mean # mean of most pulled arm
    dim = arm_kmax.feature.shape[0] # feature dimension

    th = cp.Variable(dim)
    # just want to check feasibility of constraints
    obj = cp.Minimize(cp.Constant(0))

    # recover confidence set & maximal mu over confidence set
    constr = [cp.abs(arm_kmax.feature * th  - mu_kmax) <=
              np.sqrt(self.__alpha/n_kmax*np.log(self._t-1)),
              cp.norm(th, 2) <= 1]

    noncomp = []
    for k in em_comp:
      arm = self._em_arms[k]
      problem = cp.Problem(
          obj, constr+[arm.feature * th >= a.feature * th
                       for kk, a in enumerate(self._em_arms) if k != kk])
      problem.solve(warm_start=True)

      # if constraints not satisfied, not competitive arm
      if problem.value != 0.0:
        noncomp.append(k)

    # set competitive set & do UCB
    em_comp = [item for item in em_comp if item not in noncomp]
    ucb = [arm.em_mean+np.sqrt(self.__alpha/arm.pulls*np.log(self._t-1))
           if i not in noncomp else float('-inf')
           for i, arm in enumerate(self._em_arms)]

    return np.argmax(ucb)

  def _learner_update(self, context, action, feedback):
    pass