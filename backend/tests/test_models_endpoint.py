"""
Unit tests for GET /models endpoint.

Tests verify that the models endpoint returns correct model information
including names, display names, and descriptions.
"""

import pytest
from fastapi.testclient import TestClient
from backend.api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_get_models_returns_200(client):
    """Test that GET /models returns 200 OK."""
    response = client.get("/models")
    assert response.status_code == 200


def test_get_models_returns_correct_structure(client):
    """Test that GET /models returns correct response structure."""
    response = client.get("/models")
    assert response.status_code == 200
    
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)


def test_get_models_returns_three_models(client):
    """Test that GET /models returns exactly three models."""
    response = client.get("/models")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["models"]) == 3


def test_get_models_includes_sam2(client):
    """Test that GET /models includes SAM2 model."""
    response = client.get("/models")
    assert response.status_code == 200
    
    data = response.json()
    models = data["models"]
    
    sam2_model = next((m for m in models if m["name"] == "sam2"), None)
    assert sam2_model is not None
    assert sam2_model["display_name"] == "SAM2 (Segment Anything Model)"
    assert "Foundation model" in sam2_model["description"]


def test_get_models_includes_yolov8(client):
    """Test that GET /models includes YOLOv8 model."""
    response = client.get("/models")
    assert response.status_code == 200
    
    data = response.json()
    models = data["models"]
    
    yolov8_model = next((m for m in models if m["name"] == "yolov8"), None)
    assert yolov8_model is not None
    assert yolov8_model["display_name"] == "YOLOv8 Segmentation"
    assert "Real-time" in yolov8_model["description"]


def test_get_models_includes_unet(client):
    """Test that GET /models includes U-Net model."""
    response = client.get("/models")
    assert response.status_code == 200
    
    data = response.json()
    models = data["models"]
    
    unet_model = next((m for m in models if m["name"] == "unet"), None)
    assert unet_model is not None
    assert unet_model["display_name"] == "U-Net"
    assert "encoder-decoder" in unet_model["description"]


def test_get_models_each_has_required_fields(client):
    """Test that each model has name, display_name, and description."""
    response = client.get("/models")
    assert response.status_code == 200
    
    data = response.json()
    models = data["models"]
    
    for model in models:
        assert "name" in model
        assert "display_name" in model
        assert "description" in model
        assert isinstance(model["name"], str)
        assert isinstance(model["display_name"], str)
        assert isinstance(model["description"], str)
        assert len(model["name"]) > 0
        assert len(model["display_name"]) > 0
        assert len(model["description"]) > 0


def test_get_models_names_are_unique(client):
    """Test that all model names are unique."""
    response = client.get("/models")
    assert response.status_code == 200
    
    data = response.json()
    models = data["models"]
    
    names = [m["name"] for m in models]
    assert len(names) == len(set(names))


def test_get_models_is_idempotent(client):
    """Test that calling GET /models multiple times returns same result."""
    response1 = client.get("/models")
    response2 = client.get("/models")
    
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response1.json() == response2.json()


def test_get_models_model_names_match_segment_endpoint(client):
    """Test that model names from /models match those accepted by /segment."""
    response = client.get("/models")
    assert response.status_code == 200
    
    data = response.json()
    model_names = [m["name"] for m in data["models"]]
    
    # These should match the models accepted by /segment endpoint
    expected_models = ["sam2", "yolov8", "unet"]
    assert set(model_names) == set(expected_models)
