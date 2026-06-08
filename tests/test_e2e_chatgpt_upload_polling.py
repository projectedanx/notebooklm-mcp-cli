"""End-to-end integration tests for today's added features: ChatGPT file upload and source polling."""

import pytest
from pathlib import Path
from notebooklm_tools.core.auth import load_cached_tokens
from notebooklm_tools.core.client import NotebookLMClient
from notebooklm_tools.services.sources import add_chatgpt_file_source, poll_source_content


@pytest.mark.e2e
def test_e2e_chatgpt_file_upload_and_polling():
    """Verify that downloading/uploading a ChatGPT file and polling its content works E2E."""
    # 1. Load real auth
    tokens = load_cached_tokens()
    if not tokens:
        pytest.skip("No authentication tokens available")

    client = NotebookLMClient(
        cookies=tokens.cookies, csrf_token=tokens.csrf_token, session_id=tokens.session_id
    )

    # 2. Create a temporary notebook
    notebook = client.create_notebook(title="Test E2E ChatGPT Upload")
    notebook_id = notebook.id

    try:
        # 3. Add ChatGPT file source (using the repository's LICENSE file as a public source)
        file_payload = {
            "download_url": "https://raw.githubusercontent.com/jacob-bd/notebooklm-mcp-cli/main/LICENSE",
            "file_id": "test_e2e_file_id",
            "file_name": "LICENSE.txt",
        }

        result = add_chatgpt_file_source(
            client,
            notebook_id,
            file=file_payload,
            title="E2E ChatGPT Upload License",
            wait=True,
            cleanup=True,
        )

        assert result["source_type"] == "file"
        assert result["source_id"] is not None
        assert result["title"] == "E2E ChatGPT Upload License"
        assert result["chatgpt_file"]["original_file_id"] == "test_e2e_file_id"
        assert result["chatgpt_file"]["file_name"] == "LICENSE.txt"

        # 4. Use poll_source_content to verify that text is indexed and can be retrieved
        source_id = result["source_id"]
        content_result = poll_source_content(
            client,
            source_id,
            wait=True,
            wait_timeout=60.0,
            poll_interval=3.0,
        )

        assert content_result["status"] == "success"
        assert content_result["source_id"] == source_id
        assert "MIT License" in content_result["content"]
        assert content_result["char_count"] > 0
    finally:
        # Cleanup notebook
        try:
            client.delete_notebook(notebook_id)
        except Exception:
            pass
