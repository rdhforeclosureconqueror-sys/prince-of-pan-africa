from pathlib import Path


def test_study_page_audio_download_uses_credentialed_blob_fetch():
    source = Path('src/pages/StudyPage.jsx').read_text()

    assert 'fetch(absoluteApiUrl(activeSavedAudio.downloadUrl)' in source
    assert 'credentials: "include"' in source
    assert 'await response.blob()' in source
    assert 'content-type' in source
    assert 'startsWith("audio/")' in source
    assert 'readDownloadError(response)' in source
    assert 'window.location.href = absoluteApiUrl(activeSavedAudio.downloadUrl)' not in source
