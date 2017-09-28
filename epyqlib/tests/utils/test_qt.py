import itertools

import attr
import PyQt5.QtCore

import epyqlib.utils.qt


@epyqlib.utils.qt.pyqtify()
@attr.s
class P(PyQt5.QtCore.QObject):
    a = attr.ib()
    b = attr.ib()
    c = attr.ib()

    def __attrs_post_init__(self):
        super().__init__()
        self.get = None
        self.set = None

    @PyQt5.QtCore.pyqtProperty('PyQt_PyObject')
    def pyqtify_c(self):
        x = self._pyqtify_get('c')
        self.get = True
        return x

    @pyqtify_c.setter
    def pyqtify_c(self, value):
        self.set = True
        return self._pyqtify_set('c', value)


@attr.s
class Values:
    initial = attr.ib()
    input = attr.ib()
    expected = attr.ib()
    collected = attr.ib(default=attr.Factory(list))

    def collect(self, value):
        self.collected.append(value)

    def check(self):
        return all(x == y for x, y in zip(self.expected, self.collected))


def assert_attrs_as_expected(x, values):
    assert attr.asdict(x) == {
        k: tuple(itertools.chain((v.initial,), v.expected))[-1]
        for k, v in values.items()
    }


def test_overall(qtbot):
    values = {
        'a': Values(
            initial=1,
            input=[12, 12, 13],
            expected=[12, 13],
        ),
        'b': Values(
            initial=2,
            input=[42, 42, 37],
            expected=[42, 37],
        ),
        'c': Values(
            initial=3,
            input=[4],
            expected=[4],
        ),
    }

    p = P(**{k: v.initial for k, v in values.items()})
    fields = attr.fields(P)
    assert len(fields) == len(values)

    for name, v in values.items():
        getattr(p.changed, name).connect(v.collect)

    for name, v in values.items():
        for value in v.input:
            setattr(p, name, value)

    for name, v in values.items():
        assert tuple(v.expected) == tuple(v.collected)

    assert_attrs_as_expected(p, values)

    p.c = object()
    assert p.pyqtify_c is p.c

    p.get = False
    p.c
    assert p.get

    p.set = False
    p.c = 0
    assert p.set


def test_independence(qtbot):
    ad = {'a': 1, 'b': 2, 'c': 3}
    a = P(**ad)

    bd = {'a': 10, 'b': 20, 'c': 30}
    b = P(**bd)

    assert(attr.asdict(a) == ad)
    assert(attr.asdict(b) == bd)


@epyqlib.utils.qt.pyqtify()
@attr.s
class Q(PyQt5.QtCore.QObject):
    a = attr.ib()
    b = attr.ib()

    def __attrs_post_init__(self):
        super().__init__()
        self.get = None
        self.set = None

    @PyQt5.QtCore.pyqtProperty('PyQt_PyObject')
    def pyqtify_b(self):
        return self._pyqtify_get('b')

    @pyqtify_b.setter
    def pyqtify_b(self, value):
        # self.a = min(self.a, value)
        if value < self.a:
            self.a = value

        self._pyqtify_set('b', value)


def test_property_cross_effect(qtbot):
    values = {
        'a': Values(
            initial=10,
            input=[],
            expected=[9],
        ),
        'b': Values(
            initial=20,
            input=[30, 10, 9, 20],
            expected=[30, 10, 9, 20],
        ),
    }

    p = Q(**{k: v.initial for k, v in values.items()})
    fields = attr.fields(Q)
    assert len(fields) == len(values)

    for name, v in values.items():
        getattr(p.changed, name).connect(v.collect)

    for name, v in values.items():
        for value in v.input:
            setattr(p, name, value)

    for name, v in values.items():
        assert tuple(v.expected) == tuple(v.collected)

    assert_attrs_as_expected(p, values)