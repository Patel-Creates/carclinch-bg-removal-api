from __future__ import annotations

import os
import sys
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
TESTS_DIR = THIS_FILE.parent
MOCK_DIR = TESTS_DIR / "mock"

TEST_IMAGES_DIR = TESTS_DIR / "images"
TEST_INPUT_DIR = TEST_IMAGES_DIR / "input"
TEST_OUTPUT_DIR = TEST_IMAGES_DIR / "output"

API_DIR = THIS_FILE.parents[1]  # -> api/
sys.path.insert(0, str(API_DIR))
sys.path.insert(0, str(API_DIR / "src"))

# Tell the app to write under api/test/images instead of ./images
os.environ["IMAGE_BASE_DIR"] = str(TEST_IMAGES_DIR)

import src.main as api_module  # noqa: E402


# -----------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------
def _reset_test_images_dir() -> None:
    """Delete api/test/images if it exists, then recreate input/output."""
    if TEST_IMAGES_DIR.exists():
        shutil.rmtree(TEST_IMAGES_DIR)
    TEST_INPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# fixtures
# -----------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _clean_fs_before_each_test(request: pytest.FixtureRequest):
    """
    Runs before EVERY test, EXCEPT the final 'zz' test (so artifacts remain after suite).
    """
    if request.node.name == "test_zz_upload_image_saves_files_in_input_and_output_folders":
        return
    _reset_test_images_dir()


@pytest.fixture
def client() -> TestClient:
    return TestClient(api_module.app)


# -----------------------------------------------------------------------------
# tests
# -----------------------------------------------------------------------------
def test_hello_world_endpoint(client: TestClient):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {"Hello": "World"}


def test_non_image_uploaded_returns_400_and_saves_nothing(client: TestClient):
    pdf_path = MOCK_DIR / "sample.pdf"
    assert pdf_path.exists(), f"Missing mock pdf: {pdf_path}"

    files = {"image": (pdf_path.name, pdf_path.read_bytes(), "application/pdf")}
    res = client.post("/upload-image", files=files)

    assert res.status_code == 400, res.text
    assert res.json()["detail"] == "File is not an image."
    assert list(TEST_INPUT_DIR.glob("*")) == []
    assert list(TEST_OUTPUT_DIR.glob("*")) == []


def test_invalid_extension_returns_400_and_saves_nothing(client: TestClient):
    bad_path = MOCK_DIR / "bad.txt"
    assert bad_path.exists(), f"Missing bad file: {bad_path}"

    files = {"image": (bad_path.name, bad_path.read_bytes(), "image/png")}
    res = client.post("/upload-image", files=files)

    assert res.status_code == 400, res.text
    assert res.json()["detail"] == "Invalid file extension."
    assert list(TEST_INPUT_DIR.glob("*")) == []
    assert list(TEST_OUTPUT_DIR.glob("*")) == []


def test_missing_image_returns_422(client: TestClient):
    res = client.post("/upload-image", files={})
    assert res.status_code == 422


@pytest.mark.skip(reason="requires AI model download, runs locally only")
def test_zz_upload_image_saves_files_in_input_and_output_folders(client: TestClient):
    """
    Real integration run:
    - start clean
    - send sample.jpg
    - verify 1 file in input and 1 in output
    - leave artifacts so you can visually inspect output image after the suite
    """
    # IMPORTANT: ensure this test starts clean
    _reset_test_images_dir()

    img_path = MOCK_DIR / "sample.jpg"
    assert img_path.exists(), f"Missing mock image: {img_path}"

    files = {"image": (img_path.name, img_path.read_bytes(), "image/jpeg")}
    res = client.post("/upload-image", files=files)

    assert res.status_code == 200, res.text

    input_files = list(TEST_INPUT_DIR.glob("*"))
    output_files = list(TEST_OUTPUT_DIR.glob("*"))

    assert len(input_files) == 1, f"Expected 1 input file, found: {input_files}"
    assert len(output_files) == 1, f"Expected 1 output file, found: {output_files}"

    assert input_files[0].name == "sample.jpg"
    assert output_files[0].name == "sample_processed.png"
    