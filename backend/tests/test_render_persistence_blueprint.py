from pathlib import Path


def test_render_blueprint_provisions_postgres_and_durable_audio_storage():
    blueprint = Path("config/render.yaml").read_text(encoding="utf-8")

    assert "name: prince-of-pan-africa-db" in blueprint
    assert "databaseName: prince_of_pan_africa" in blueprint
    assert "user: prince_of_pan_africa" in blueprint
    assert "key: DATABASE_URL" in blueprint
    assert "fromDatabase:" in blueprint
    assert "name: prince-of-pan-africa-db" in blueprint
    assert "property: connectionString" in blueprint
    assert "key: AUDIO_STORAGE_DIR" in blueprint
    assert "value: /var/data/static/audio" in blueprint
    assert "disk:" in blueprint
    assert "mountPath: /var/data" in blueprint
