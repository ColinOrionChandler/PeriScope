from periscope.app import keep_angle_excluding


def test_keep_angle_excluding_non_wrapped_range():
    assert keep_angle_excluding(50, 60, 260)
    assert not keep_angle_excluding(120, 60, 260)
    assert keep_angle_excluding(300, 60, 260)


def test_keep_angle_excluding_wrapped_range():
    assert not keep_angle_excluding(350, 300, 60)
    assert not keep_angle_excluding(30, 300, 60)
    assert keep_angle_excluding(180, 300, 60)


def test_keep_angle_excluding_rejects_range_boundaries():
    assert not keep_angle_excluding(60, 60, 260)
    assert not keep_angle_excluding(260, 60, 260)
    assert not keep_angle_excluding(300, 300, 60)
    assert not keep_angle_excluding(60, 300, 60)
