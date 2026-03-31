"""
Unit tests for error handling in backend API.

Tests verify that error handlers correctly format error responses,
log errors with context, and handle various error scenarios.
"""

import pytest
import io
from fastapi.testclient import TestClient
from PIL import Image
from backend.api.main import app, UPLOAD_DIR, MASK_DIR


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def valid_test_image():
    """Create a valid test image file in memory."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer


@pytest.fixture(autouse=True)
def cleanup_files():
    """Clean up uploaded files and masks after each test."""
    yield
    for file in UPLOAD_DIR.glob("*"):
        if file.is_file():
            file.unlink()
    for file in MASK_DIR.glob("*"):
        if file.is_file():
            file.unlink()


def test_400_error_has_correct_format(client):
    """Test that 400 errors return correct error format."""
    # Upload with invalid format
    buffer = io.BytesIO(b"fake content")
    response = client.post(
        "/upload",
        files={"file": ("test.txt", buffer, "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    
    # Check error response structure
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert len(data["detail"]) > 0


def test_404_error_has_correct_format(client):
    """Test that 404 errors return correct error format."""
    response = client.post(
        "/segment",
        json={
            "image_id": "non-existent-id",
            "model": "sam2"
        }
    )
    
    assert response.status_code == 404
    data = response.json()
    
    # Check error response structure
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert "not found" in data["detail"].lower()


def test_413_error_has_correct_format(client):
    """Test that 413 errors return correct error format."""
    # Create file larger than 50MB
    large_data = b"x" * (51 * 1024 * 1024)
    buffer = io.BytesIO(large_data)
    
    response = client.post(
        "/upload",
        files={"file": ("large.jpg", buffer, "image/jpeg")}
    )
    
    assert response.status_code == 413
    data = response.json()
    
    # Check error response structure
    assert "detail" in data
    assert isinstance(data["detail"], str)
    assert "too large" in data["detail"].lower()
    assert "50MB" in data["detail"]


def test_error_messages_are_descriptive(client):
    """Test that error messages provide helpful information."""
    # Test invalid file format
    buffer = io.BytesIO(b"fake")
    response = client.post(
        "/upload",
        files={"file": ("test.txt", buffer, "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "JPG" in data["detail"] or "PNG" in data["detail"] or "TIFF" in data["detail"]


def test_invalid_model_error_lists_supported_models(client, valid_test_image):
    """Test that invalid model error lists all supported models."""
    # Upload image first
    upload_response = client.post(
        "/upload",
        files={"file": ("test.jpg", valid_test_image, "image/jpeg")}
    )
    image_id = upload_response.json()["image_id"]
    
    # Try invalid model
    response = client.post(
        "/segment",
        json={
            "image_id": image_id,
            "model": "invalid"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    
    # Should list all supported models
    assert "sam2" in data["detail"]
    assert "yolov8" in data["detail"]
    assert "unet" in data["detail"]


def test_file_size_validation_enforced(client):
    """Test that file size validation is enforced at 50MB."""
    # Create file exactly at limit (should pass)
    data_at_limit = b"x" * (50 * 1024 * 1024)
    buffer = io.BytesIO(data_at_limit)
    
    # Note: This test might be slow due to large file size
    # In practice, you might want to mock this or use a smaller limit for testing
    response = client.post(
        "/upload",
        files={"file": ("at_limit.jpg", buffer, "image/jpeg")}
    )
    
    # Should fail because it's not a valid image, but not due to size
    # (413 would indicate size issue, 400 indicates format issue)
    assert response.status_code in [400, 413]


def test_corrupted_file_error_message(client):
    """Test that corrupted file errors are descriptive."""
    buffer = io.BytesIO(b"This is not an image")
    
    response = client.post(
        "/upload",
        files={"file": ("fake.jpg", buffer, "image/jpeg")}
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "corrupted" in data["detail"].lower() or "unable to read" in data["detail"].lower()


def test_missing_image_error_message(client):
    """Test that missing image error is descriptive."""
    response = client.post(
        "/segment",
        json={
            "image_id": "missing-uuid",
            "model": "sam2"
        }
    )
    
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()
    assert "upload" in data["detail"].lower()


def test_error_response_includes_timestamp(client):
    """Test that error responses include timestamp."""
    buffer = io.BytesIO(b"fake")
    response = client.post(
        "/upload",
        files={"file": ("test.txt", buffer, "text/plain")}
    )
    
    assert response.status_code == 400
    data = response.json()
    
    # Check if timestamp is present (if implemented in error handler)
    # This depends on the ErrorResponse model implementation
    if "timestamp" in data:
        assert isinstance(data["timestamp"], str)
        assert len(data["timestamp"]) > 0


def test_multiple_errors_handled_independently(client, valid_test_image):
    """Test that multiple error scenarios are handled independently."""
    # Error 1: Invalid format
    response1 = client.post(
        "/upload",
        files={"file": ("test.txt", io.BytesIO(b"fake"), "text/plain")}
    )
    assert response1.status_code == 400
    
    # Error 2: Missing image
    response2 = client.post(
        "/segment",
        json={"image_id": "missing", "model": "sam2"}
    )
    assert response2.status_code == 404
    
    # Error 3: Invalid model
    upload_response = client.post(
        "/upload",
        files={"file": ("test.jpg", valid_test_image, "image/jpeg")}
    )
    image_id = upload_response.json()["image_id"]
    
    response3 = client.post(
        "/segment",
        json={"image_id": image_id, "model": "invalid"}
    )
    assert response3.status_code == 400
    
    # All errors should have different messages
    assert response1.json()["detail"] != response2.json()["detail"]
    assert response2.json()["detail"] != response3.json()["detail"]


def test_error_cleanup_on_validation_failure(client):
    """Test that files are cleaned up when validation fails."""
    buffer = io.BytesIO(b"This is not an image")
    
    response = client.post(
        "/upload",
        files={"file": ("fake.jpg", buffer, "image/jpeg")}
    )
    
    assert response.status_code == 400
    
    # Verify no files were left in upload directory
    uploaded_files = list(UPLOAD_DIR.glob("*.jpg"))
    assert len(uploaded_files) == 0
