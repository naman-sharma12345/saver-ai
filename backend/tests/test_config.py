from config import database_uri


def test_database_url_postgres_scheme_is_normalised(monkeypatch):
    monkeypatch.delenv('DATABASE_URI', raising=False)
    monkeypatch.setenv('DATABASE_URL', 'postgres://u:p@h:5432/db')
    assert database_uri() == 'postgresql://u:p@h:5432/db'


def test_database_uri_wins_and_sqlite_default(monkeypatch):
    monkeypatch.setenv('DATABASE_URI', 'postgresql://a/b')
    monkeypatch.setenv('DATABASE_URL', 'postgres://x/y')
    assert database_uri() == 'postgresql://a/b'
    monkeypatch.delenv('DATABASE_URI')
    monkeypatch.delenv('DATABASE_URL')
    assert database_uri().startswith('sqlite:///')
