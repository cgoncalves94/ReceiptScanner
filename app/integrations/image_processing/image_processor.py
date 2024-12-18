import logging
from pathlib import Path

import cv2
from PIL import Image

logger = logging.getLogger(__name__)


class ImageProcessor:
    @staticmethod
    def validate_image(image: Image.Image) -> None:
        """Validate image format and dimensions."""
        # Validate image format
        if not isinstance(image, Image.Image):
            raise ValueError("Invalid image format")

        # Validate minimum dimensions
        min_width, min_height = 100, 100
        if image.width < min_width or image.height < min_height:
            raise ValueError(
                f"Image dimensions too small: {image.width}x{image.height}"
            )

    @staticmethod
    def preprocess_image(image_path: str) -> Image.Image:
        """
        Very gently preprocess the receipt image to enhance readability while maintaining quality:
        1. Convert to grayscale
        2. Minimal contrast enhancement
        Returns a PIL Image that can be used directly with Gemini.
        """
        # Read the image
        logger.info(f"Reading image from {image_path}")
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to read image from {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Very gentle contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)

        # Convert back to PIL Image
        pil_image = Image.fromarray(enhanced)

        # Validate the processed image
        ImageProcessor.validate_image(pil_image)
        return pil_image

    @staticmethod
    def save_processed_image(processed_image: Image.Image, output_path: str) -> str:
        """Save the processed image for record keeping."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        processed_image.save(output_path)
        return output_path
