import numpy as np
import cv2
from .profiler import timed

@timed
def align_and_crop(img, landmarks, image_size=112):
    """
    Align and crop the face from the image based on the given landmarks.

    Args:
        img (np.ndarray): The full image (not the cropped bounding box). This image will be transformed.
        landmarks (List[np.ndarray]): List of 5 keypoints (landmarks) as (x, y) coordinates. These keypoints typically include the eyes, nose, and mouth.
        image_size (int, optional): The size to which the image should be resized. Defaults to 112. It is typically either 112 or 128 for face recognition models.

    Returns:
        Tuple[np.ndarray, np.ndarray]: The aligned face image and the transformation matrix.
    """
    # Define the reference keypoints used in ArcFace model, based on a typical facial landmark set.
    _arcface_ref_kps = np.array(
        [
            [38.2946, 51.6963],  # Left eye
            [73.5318, 51.5014],  # Right eye
            [56.0252, 71.7366],  # Nose
            [41.5493, 92.3655],  # Left mouth corner
            [70.7299, 92.2041],  # Right mouth corner
        ],
        dtype=np.float32,
    )

    # Ensure the input landmarks have exactly 5 points (as expected for face alignment)
    assert len(landmarks) == 5

    # Validate that image_size is divisible by either 112 or 128 (common image sizes for face recognition models)
    assert image_size % 112 == 0 or image_size % 128 == 0

    # Adjust the scaling factor (ratio) based on the desired image size (112 or 128)
    if image_size % 112 == 0:
        ratio = float(image_size) / 112.0
        diff_x = 0  # No horizontal shift for 112 scaling
    else:
        ratio = float(image_size) / 128.0
        diff_x = 8.0 * ratio  # Horizontal shift for 128 scaling

    # Apply the scaling and shifting to the reference keypoints
    dst = _arcface_ref_kps * ratio
    dst[:, 0] += diff_x  # Apply the horizontal shift

    # Estimate the similarity transformation matrix to align the landmarks with the reference keypoints
    M, inliers = cv2.estimateAffinePartial2D(np.array(landmarks), dst, ransacReprojThreshold=1000)
    assert np.all(inliers == True)
    
    # Apply the affine transformation to the input image to align the face
    aligned_img = cv2.warpAffine(img, M, (image_size, image_size), borderValue=0.0)

    return aligned_img, M