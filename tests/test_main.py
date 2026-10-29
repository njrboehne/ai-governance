from ai_governance import cli, main
from ai_governance.errors import IngestError


def test_no_subcommand_prints_help(capsys):
    assert main([]) == 0
    assert "ingest" in capsys.readouterr().out


def test_failure_returns_1_with_message(monkeypatch, tmp_path, capsys):
    def fail(*args, **kwargs):
        raise IngestError("boom")

    monkeypatch.setattr(cli, "fetch", fail)
    assert main(["ingest", "--data-dir", str(tmp_path)]) == 1
    assert "boom" in capsys.readouterr().err
    assert not (tmp_path / "chunks.jsonl").exists()
