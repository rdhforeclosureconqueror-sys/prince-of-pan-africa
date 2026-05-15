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


def test_study_page_generation_polling_stops_on_partially_complete():
    source = Path('src/pages/StudyPage.jsx').read_text()

    assert 'isGenerationTerminal(progressState)' in source
    assert '["complete", "failed", "partially_complete"].includes(progressState?.status)' in source
    assert 'const activeStatuses = new Set(["pending", "chunking", "generating_chapters"]);' in source
    assert 'window.setTimeout(pollGenerationStatus, 3000)' in source
    assert 'window.setInterval' not in source
    assert 'let inFlight = false' in source
    assert 'if (cancelled || inFlight) return' in source
    assert 'Completed with errors' in source


def test_study_page_download_errors_are_user_specific():
    source = Path('src/pages/StudyPage.jsx').read_text()

    assert 'Audio download is not authorized. Please sign in with access to this audiobook.' in source
    assert 'Audio file is missing from storage. Please regenerate this chapter.' in source
    assert 'Audio generation is not complete for this chapter yet.' in source
