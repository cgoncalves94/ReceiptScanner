import logging
from pathlib import Path

import cv2
from PIL import Image

logger = logging.getLogger(__name__)


class ImageProcessor:
    @staticmethod
    def preprocess_image(image_path: str) -> Image.Image:
        """
        Very gently preprocess the receipt image to enhance readability while maintaining quality:
        1. Convert to grayscale
        2. Minimal contrast enhancement
        Returns a PIL Image that can be used directly with Gemini.
        """
        try:
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

            return pil_image

        except Exception as e:
            logger.error(f"Error preprocessing image: {str(e)}")
            raise

    @staticmethod
    def save_processed_image(processed_image: Image.Image, output_path: str) -> str:
        """Save the processed image for record keeping."""
        try:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            processed_image.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"Error saving processed image: {str(e)}")
            raise
