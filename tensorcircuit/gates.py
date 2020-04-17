"""Declarations of single qubit and two-qubit gates."""

import sys
from copy import deepcopy
from typing import Optional
from functools import partial

import numpy as np
from scipy.linalg import expm
from scipy.stats import unitary_group
import tensornetwork as tn

from .cons import npdtype

thismodule = sys.modules[__name__]

# Common single qubit states as np.ndarray objects
zero_state = np.array([1.0, 0.0], dtype=npdtype)
one_state = np.array([0.0, 1.0], dtype=npdtype)
plus_state = 1.0 / np.sqrt(2) * (zero_state + one_state)
minus_state = 1.0 / np.sqrt(2) * (zero_state - one_state)

# Common single qubit gates as np.ndarray objects
_h_matrix = 1 / np.sqrt(2) * np.array([[1.0, 1.0], [1.0, -1.0]])
_i_matrix = np.array([[1.0, 0.0], [0.0, 1.0]])
_x_matrix = np.array([[0.0, 1.0], [1.0, 0.0]])
_y_matrix = np.array([[0.0, -1j], [1j, 0.0]])
_z_matrix = np.array([[1.0, 0.0], [0.0, -1.0]])

_cnot_matrix = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 1.0, 0.0],
    ]
)
_cz_matrix = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, -1.0],
    ]
)
_swap_matrix = np.array(
    [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
)


def template(m, n) -> tn.Node:
    return tn.Node(deepcopy(m), name=n)


def meta_gate():
    for name in dir(thismodule):
        if name.endswith("_matrix") and name.startswith("_"):
            n = name[1:-7]
            m = getattr(thismodule, name)
            if m.shape[0] == 4:
                m = np.reshape(m, newshape=(2, 2, 2, 2))
            m = m.astype(npdtype)
            temp = partial(template, m, n)
            setattr(thismodule, n + "gate", temp)
            setattr(thismodule, n, temp)


meta_gate()


def rgate(seed: Optional[int] = None, angle_scale: float = 1.0):
    """Returns the random single qubit gate described in https://arxiv.org/abs/2002.07730.

    Args:
        seed: Seed for random number generator.
        angle_scale: Floating point value to scale angles by. Default 1.

    """
    if seed:
        np.random.seed(seed)

    # Get the random parameters
    theta, alpha, phi = np.random.rand(3) * 2 * np.pi
    mx = np.sin(alpha) * np.cos(phi)
    my = np.sin(alpha) * np.sin(phi)
    mz = np.cos(alpha)

    theta *= angle_scale

    # Get the unitary
    unitary = expm(-1j * theta * (mx * _x_matrix + my * _y_matrix * mz * _z_matrix))

    return tn.Node(unitary)


r = rgate


def random_two_qubit_gate(seed: Optional[int] = None) -> tn.Node:
    """Returns a random two-qubit gate.

    Args:
        seed: Seed for random number generator.
    """
    if seed:
        np.random.seed(seed)
    unitary = unitary_group.rvs(dim=4)
    unitary = np.reshape(unitary, newshape=(2, 2, 2, 2))
    return tn.Node(deepcopy(unitary), name="R2Q")