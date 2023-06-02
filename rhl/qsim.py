from typing import Any
import numpy as np

from . import objects


X = np.array([
    [0, 1],
    [1, 0]
])

H = 1 / np.sqrt(2) * np.array([
    [1, 1],
    [1, -1]
])


class QSimulator(objects.Object):
    NUM_QUBITS = 3

    def __init__(self):
        self.free_qubits = list(range(self.NUM_QUBITS))
        self.state_vector = np.zeros(2 ** self.NUM_QUBITS)
        self.state_vector[0] = 1

    def qalloc(self, length: int) -> list[int]:
        if length > len(self.free_qubits):
            raise Exception("Not enough qubits")

        allocated, self.free_qubits = self.free_qubits[:length], self.free_qubits[length:]
        for qubit in allocated:
            self._reset(qubit)
        return allocated

    def qfree(self, qubits: list[int]) -> None:
        self.free_qubits += qubits

    def _reset(self, qubit: int) -> None:
        val = self.measure(qubit)
        if val == 1:
            self.x(qubit)

    def measure(self, qubit: int) -> int:
        zeros, ones = self._divide_by(qubit)
        prob_zeros = zeros.dot(zeros)
        prob_ones = ones.dot(ones)

        rand_number = np.random.random()
        if rand_number < prob_zeros:
            self.state_vector = zeros / np.sqrt(prob_zeros)
            return 0
        else:
            self.state_vector = ones / np.sqrt(prob_ones)
            return 1

    def _divide_by(self, qubit: int) -> Any:
        zeros = np.zeros(2 ** self.NUM_QUBITS)
        ones = np.zeros(2 ** self.NUM_QUBITS)

        for i in range(2 ** self.NUM_QUBITS):
            if (i >> qubit) % 2 == 0:
                zeros[i] = self.state_vector[i]
            else:
                ones[i] = self.state_vector[i]

        return zeros, ones

    def x(self, qubit: int) -> None:
        op = self._kron_product(X, qubit)
        self.state_vector = op @ self.state_vector

    def h(self, qubit: int) -> None:
        op = self._kron_product(H, qubit)
        self.state_vector = op @ self.state_vector

    def _kron_product(self, op: np.array, qubit: int) -> np.array:
        return np.kron(
            np.eye(2 ** (self.NUM_QUBITS - qubit - 1)),
            np.kron(
                op,
                np.eye(2 ** qubit)
            )
        )

    def cx(self, control: int, target: int) -> None:
        op = np.zeros((2 ** self.NUM_QUBITS, 2 ** self.NUM_QUBITS))

        for state in range(2 ** self.NUM_QUBITS):
            to_state = state
            if (state >> control) % 2 == 1:
                to_state ^= 1 << target

            op[to_state, state] = 1

        self.state_vector = op @ self.state_vector

    def mcz(self, qubits: list[int]) -> None:
        op = np.eye(2 ** self.NUM_QUBITS)

        for state in range(2 ** self.NUM_QUBITS):
            if all((state >> qubit) % 2 == 1 for qubit in qubits):
                op[state, state] = -1

        self.state_vector = op @ self.state_vector

    def to_string(self) -> str:
        return "QSimulator"
