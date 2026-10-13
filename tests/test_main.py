from ai_governance import main


def test_main_prints_status(capsys):
    main()
    assert "in progress" in capsys.readouterr().out
