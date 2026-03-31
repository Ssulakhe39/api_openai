"""
OpenAI GPT-4.1 Vision-based building boundary detector.

Sends the segmentation mask to GPT-4.1 Vision and parses
the returned polygon coordinates to overlay on the original image.
"""

import base64
import json
import re
import os
import numpy as np
import cv2
from typing import List, Dict
from openai import OpenAI


BOUNDARY_PROMPT = (
    "You are a geospatial AI that extracts building footprints from segmentation masks. "
    "The image contains white building regions on a black background. "
    "Detect each building and return its boundary polygon coordinates in pixel space. "
    "Return only JSON in the format:\n"
    '{ "buildings": [ {"polygon": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]} ] }'
)


class OpenAIBoundaryDetector:
    """
    Uses GPT-4.1 Vision to detect building boundary polygons from a segmentation mask.
    """

    def __init__(self, api_key: str | None = None, model: str = "gpt-4.1"):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not set. Add it to backend/.env")
        self.client = OpenAI(api_key=key)
        self.model = model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_from_mask(self, mask: np.ndarray) -> List[Dict]:
        """
        Send mask to GPT-4.1 Vision and return list of building dicts.

        Args:
            mask: Grayscale or binary mask (H, W) or (H, W, 3)

        Returns:
            List of dicts: [{"id": int, "coordinates": [[x,y], ...]}, ...]
        """
        b64 = self._encode_mask(mask)
        raw_json = self._call_vision_api(b64)
        buildings = self._parse_response(raw_json)
        return buildings

    def overlay_on_image(
        self,
        image: np.ndarray,
        buildings: List[Dict],
        color: tuple = (0, 255, 0),
        thickness: int = 2,
    ) -> np.ndarray:
        """
        Draw polygon boundaries on the original image using cv2.polylines.

        Args:
            image: BGR or RGB image (H, W, 3)
            buildings: Output of detect_from_mask()
            color: Line color in BGR (default green)
            thickness: Line thickness in pixels

        Returns:
            Image with polygons drawn
        """
        result = image.copy()
        for building in buildings:
            coords = building.get("coordinates", [])
            if len(coords) < 2:
                continue
            pts = np.array(coords, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(result, [pts], isClosed=True, color=color, thickness=thickness)
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _encode_mask(self, mask: np.ndarray) -> str:
        """Encode mask ndarray as base64 PNG string."""
        # Ensure uint8
        if mask.dtype != np.uint8:
            mask = mask.astype(np.uint8)

        # Convert to grayscale if RGB
        if len(mask.shape) == 3:
            mask = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)

        # Encode to PNG bytes
        success, buf = cv2.imencode(".png", mask)
        if not success:
            raise RuntimeError("Failed to encode mask as PNG")

        return base64.b64encode(buf.tobytes()).decode("utf-8")

    def _call_vision_api(self, b64_image: str) -> str:
        """Send base64 image to GPT-4.1 Vision and return raw text response."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": BOUNDARY_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    def _parse_response(self, text: str) -> List[Dict]:
        """
        Parse GPT response text into list of building dicts.

        Handles cases where the model wraps JSON in markdown code fences.
        """
        # Strip markdown code fences if present
        cleaned = re.sub(r"```(?:json)?", "", text).strip().rstrip("`").strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try to extract JSON object from surrounding text
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if not match:
                raise ValueError(f"Could not parse JSON from GPT response:\n{text}")
            data = json.loads(match.group())

        raw_buildings = data.get("buildings", [])
        buildings = []
        for idx, b in enumerate(raw_buildings):
            polygon = b.get("polygon", [])
            if len(polygon) < 3:
                continue
            buildings.append({
                "id": idx + 1,
                "coordinates": polygon,
                "num_points": len(polygon),
            })

        return buildings
