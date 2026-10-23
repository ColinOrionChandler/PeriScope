from periscope.ephemeris import _latest_ambiguous_record_id


def test_latest_ambiguous_record_id_prefers_latest_matching_primary():
    message = """
    Ambiguous target name; provide unique id:
        Record #  Epoch-yr  >MATCH DESIG<  Primary Desig  Name
        --------  --------  -------------  -------------  -------------------------
        90001170    2009    213P           213P            Van Ness
        90001171    2018    213P           213P            Van Ness
        90001172    2011    213P-B         213P-B          Van Ness
    """

    assert _latest_ambiguous_record_id("213P", message) == "90001171"


def test_latest_ambiguous_record_id_handles_space_designations():
    message = """
    Ambiguous target name; provide unique id:
        Record #  Epoch-yr  >MATCH DESIG<  Primary Desig  Name
        --------  --------  -------------  -------------  -------------------------
        90009990    2000    P/2000 R2      P/2000 R2       LINEAR
        90009991    2004    P/2000 R2      P/2000 R2       LINEAR
        90009992    2001    P/2000 R2-B    P/2000 R2-B     LINEAR
    """

    assert _latest_ambiguous_record_id("P/2000 R2", message) == "90009991"


def test_latest_ambiguous_record_id_ignores_unrelated_errors():
    assert _latest_ambiguous_record_id("16P", "No ephemeris meets criteria") is None
