from lib.project import unproject

def test_unproject():
    # This test fails on my MacOS, no idea why, must be my local python setup
    assert(unproject([-76.521714, 36.330247])) == (36.330247, -76.521714)
