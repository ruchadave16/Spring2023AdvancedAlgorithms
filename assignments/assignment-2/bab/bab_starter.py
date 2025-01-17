import picos as pic
from picos import RealVariable
from copy import deepcopy
from heapq import *
import heapq as hq
import numpy as np
import itertools
import math

counter = itertools.count()


class BBTreeNode:
    """
    Creates and handles a BBTreeNode object that can branch and bound
    to determine the optimal result and corresponding best variable
    values.

    Attributes:
        vars (list of picos RealVariable objects): variables in the
            problem.
        constraints (list of constraints): list of problem constraints.
            ex: [z == x+y, -5*x+4*y <= 0, 6*x+2*y <= 17, x>=0, y>=0].
        objective (picos RealVariable object): variable that is being
            maximized.
        prob (picos Problem object): problem created by buildProblem
            using constraints, vars, and objective.
    """

    def __init__(self, vars=[], constraints=[], objective="", prob=None):
        """
        Initializes BBTreeNode.
        """
        self.vars = vars
        self.constraints = constraints
        self.objective = objective
        self.prob = prob

    def __deepcopy__(self, var):
        """
        Deepcopies the picos problem.
        This overrides the system's deepcopy method bc it doesn't work
        on classes by itself.

        Returns:
            (BBTreeNode object): copy of BBTreeNode.
        """
        newprob = pic.Problem.clone(self.prob)
        return BBTreeNode(self.vars, newprob.constraints, self.objective, newprob)

    def buildProblem(self):
        """
        Builds the initial Picos problem.

        Returns:
            self.prob (picos Problem object): problem created from
                constraints, objective, and vars.
        """
        prob = pic.Problem()
        prob.add_list_of_constraints(self.constraints)
        prob.set_objective("max", self.objective)
        self.prob = prob
        return self.prob

    def is_integral(self):
        """
        Checks if all variables (excluding the one we're maxing) are
        integers.

        Returns:
            (bool): returns True if all variables (excluding the one
                we're maximizing) are integers, otherwise False.
        """
        for v in self.vars[:-1]:
            if v.value == None or abs(round(v.value) - float(v.value)) > 1e-4:
                return False
        return True

    def branch_floor(self, branch_var):
        """
        Makes a child where xi <= floor(xi).

        Args:
            branch_var (float): variable to branch on.

        Returns:
            n1 (BBTreeNode object): child where xi <= floor(xi).
        """
        n1 = self.__deepcopy__(branch_var)
        # add in the new binary constraint
        n1.prob.add_constraint(branch_var <= math.floor(branch_var.value))
        return n1

    def branch_ceil(self, branch_var):
        """
        Makes a child where xi >= ceiling(xi).

        Args:
            branch_var (float): variable to branch on.

        Returns:
            n2 (BBTreeNode object): child where xi >= ceiling(xi).
        """
        n2 = self.__deepcopy__(branch_var)
        # add in the new binary constraint
        n2.prob.add_constraint(branch_var >= math.ceil(branch_var.value))
        return n2

    def bbsolve(self):
        """
        Uses the branch and bound method to solve an integer program.

        Returns:
            bestres (float): value of the maximized objective function.
            bestnode_vars (list of floats): list of variables that
                create bestres.
        """
        # Build up the initial problem and add it to a heap
        root = self
        res = root.buildProblem().solve(solver="cvxopt")
        heap = [(res, next(counter), root)]

        # Set bestres to an arbitrary small initial best objective value
        bestres = -1e20

        # Initialize bestnode_vars to the root vars
        bestnode_vars = root.vars

        while len(heap) > 0:
            _, _, thisres = hq.heappop(heap)

            for var in thisres.vars:
                print(var.value)

            # If integer answer, check for best result
            if thisres.is_integral():
                bestres = thisres.objective.value
                bestnode_vars = thisres.vars

            # If current answer is better than best result
            elif thisres.objective.value > bestres:

                # Pick variable to branch on
                chosen_var = thisres.vars[0]
                for var in thisres.vars:
                    if abs(round(var.value) - float(var.value)) > 1e-4:
                        chosen_var = var
                        print(chosen_var)
                        break

                # Create new branches
                n1 = thisres.branch_floor(chosen_var)
                n2 = thisres.branch_ceil(chosen_var)

                # Add to heap if feasible
                try:
                    if n1.prob.solve(solver="cvxopt") != "infeasible":
                        hq.heappush(heap, (bestres, next(counter), n1))
                except:
                    pass

                try:
                    if n2.prob.solve(solver="cvxopt") != "infeasible":
                        hq.heappush(heap, (bestres, next(counter), n2))
                except:
                    pass

            # Skip bad solutions
            else:
                pass

        return bestres, bestnode_vars
