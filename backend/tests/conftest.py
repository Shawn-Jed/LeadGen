import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import leadtool  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    """Frisches tmp-Repo mit pipeline.md + templates/lead.md."""
    leadtool.init_repo(tmp_path)
    return tmp_path
