"""
module for functions adding layers of circuits
"""

import sys
import itertools
import numpy as np
import networkx as nx
from typing import Sequence, Union, Callable, Any, Optional

from ..circuit import Circuit

thismodule = sys.modules[__name__]

Tensor = Any  # tf.Tensor
Graph = Any  # nx.Graph


def generate_double_gate(gates: str) -> None:
    d1, d2 = gates[0], gates[1]

    def f(
        circuit: Circuit, qubit1: int, qubit2: int, symbol: Union[Tensor, float]
    ) -> Circuit:
        if d1 == "x":
            circuit.H(qubit1)  # type: ignore
        elif d1 == "y":
            circuit.rx(qubit1, theta=-np.pi / 2)  # type: ignore
        if d2 == "x":
            circuit.H(qubit2)  # type: ignore
        elif d2 == "y":
            circuit.rx(qubit2, theta=-np.pi / 2)  # type: ignore
        circuit.CNOT(qubit1, qubit2)  # type: ignore
        circuit.rz(qubit2, theta=symbol)  # type: ignore
        circuit.CNOT(qubit1, qubit2)  # type: ignore
        if d1 == "x":
            circuit.H(qubit1)  # type: ignore
        elif d1 == "y":
            circuit.rx(qubit1, theta=np.pi / 2)  # type: ignore
        if d2 == "x":
            circuit.H(qubit2)  # type: ignore
        elif d2 == "y":
            circuit.rx(qubit2, theta=np.pi / 2)  # type: ignore
        return circuit

    f.__doc__ = """%sgate""" % gates
    setattr(thismodule, gates + "gate", f)


def generate_gate_layer(gate: str) -> None:
    """
    $$e^{-i\theta \sigma}$$

    :param gate:
    :return:
    """

    def f(
        circuit: Circuit, symbol: Union[Tensor, float] = None, g: Graph = None
    ) -> Circuit:  # compatible with graph mode
        if gate.lower() in Circuit.sgates:
            for n in range(circuit._nqubits):
                getattr(circuit, gate)(n)
        else:
            for n in range(circuit._nqubits):
                getattr(circuit, gate)(n, theta=2 * symbol)  # type: ignore
        return circuit

    f.__doc__ = """%slayer""" % gate
    f.__repr__ = """%slayer""" % gate  # type: ignore
    f.__trainable__ = False if gate in Circuit.sgates else True  # type: ignore
    setattr(thismodule, gate + "layer", f)


def generate_double_gate_layer(gates: str) -> None:
    def f(circuit: Circuit, symbol: Union[Tensor, float], g: Graph = None) -> Circuit:
        if g is None:
            g = nx.complete_graph(circuit._nqubits)
        for e in g.edges:
            qubit1, qubit2 = e
            getattr(thismodule, gates + "gate")(
                circuit, qubit1, qubit2, -symbol * g[e[0]][e[1]].get("weight", 1.0) * 2
            )  ## should be better as * 2 # e^{-i\theta H}, H=-ZZ
        return circuit

    f.__doc__ = """%slayer""" % gates
    f.__repr__ = """%slayer""" % gates  # type: ignore
    f.__trainable__ = True  # type: ignore
    setattr(thismodule, gates + "layer", f)


for gate in ["rx", "ry", "rz", "H"]:
    generate_gate_layer(gate)

for gates in itertools.product(*[["x", "y", "z"] for _ in range(2)]):
    gates = gates[0] + gates[1]
    generate_double_gate(gates)  # type: ignore
    generate_double_gate_layer(gates)  # type: ignore

_cset: Sequence[Callable[[Circuit, Union[Tensor, float], Graph], Circuit]] = []


def set_choice(
    l: Optional[
        Sequence[Callable[[Circuit, Union[Tensor, float], Graph], Circuit]]
    ] = None
) -> None:
    global _cset

    if not l:
        _cset = [Hlayer, rxlayer, rzlayer, zzlayer]  # type: ignore
    else:
        _cset = l


set_choice()


def get_choice() -> Sequence[Callable[[Circuit, Union[Tensor, float], Graph], Circuit]]:
    return _cset
