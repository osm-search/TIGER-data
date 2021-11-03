from lib.project import unproject

def test_unproject():
    assert(unproject([-76.521714, 36.330247])) == (36.330247, -76.521714)
