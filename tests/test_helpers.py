import pytest

from lib.helpers import round_point, adjacent, glom

def test_round_point():
  assert round_point([1.0, 1.0]) == (1.0, 1.0)
  assert round_point([12.345, 56.789], 1) == (12.3, 56.8)

def test_adjacent():
  line1 = [[1,1], [1,5]]
  line2 = [[2,2], [1,5]]
  line3 = [[2,2], [1,1]]
  line4 = [[5,6], [6,5]]
  assert adjacent(line1, line2) is True
  assert adjacent(line1, line3) is True
  assert adjacent(line1, line4) is False

def test_glom():
  line1 = [[1,1], [1,2], [1,3]]
  line2 = [[2,2], [2,3], [1,3]]

  # line1 + reversed line2
  assert glom(line1, line2) == [[1,1], [1,2], [1,3], [2,3], [2,2]]

