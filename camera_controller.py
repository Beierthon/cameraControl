import cv2
import datetime
import time # For time.sleep
import os
import zivid

def analyze_image_quality(image_path: str):
    """
    Analyzes the quality of a 3D printed object from an image.
    Uses STL-vs-PointCloud comparison and voxel analysis.
    """
    print(f"Analyzing image: {image_path}")
    from supabase_client import QUALITY_STATUS_GOOD, QUALITY_STATUS_BAD, QUALITY_STATUS_UNCERTAIN
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), 'analysis'))
    from analysis.compare_stl_pointcloud import compare_stl_and_pointcloud
    from analysis.voxel_analysis import voxel_analysis

    # Define paths
    stl_path = os.path.join(os.path.dirname(__file__), 'data', 'raw', 'CAD.stl')
    ply_path = os.path.join(os.path.dirname(__file__), 'data', 'raw', 'PointCloud.ply')

    # Check if files exist
    if not os.path.exists(stl_path) or not os.path.exists(ply_path):
        print(f"Error: STL or PLY file not found. STL: {stl_path}, PLY: {ply_path}")
        return 0.0, QUALITY_STATUS_UNCERTAIN

    # Run comparison
    try:
        points_with_distances_df, stats = compare_stl_and_pointcloud(stl_path, ply_path)
        voxel_df = voxel_analysis(points_with_distances_df)
    except Exception as e:
        print(f"Error during STL/PLY analysis: {e}")
        return 0.0, QUALITY_STATUS_UNCERTAIN

    # Use mean of mean_distance as quality score
    if voxel_df.empty:
        print("Voxel analysis returned no data.")
        return 0.0, QUALITY_STATUS_UNCERTAIN
    quality_score = 100.0 - 1000.0 * voxel_df['mean_distance'].mean()  # Example: lower mean_distance = higher score
    quality_score = max(0.0, min(100.0, quality_score))

    # Determine quality status
    quality_status_id = QUALITY_STATUS_UNCERTAIN
    if quality_score >= 90.0:
        quality_status_id = QUALITY_STATUS_GOOD
    elif quality_score < 70.0:
        quality_status_id = QUALITY_STATUS_BAD

    print(f"Analysis result: Score={quality_score:.2f}, Status ID={quality_status_id}")
    return quality_score, quality_status_id

def take_photo_with_zivid(output_dir: str = "images"):
    """Captures an image and point cloud from the Zivid camera and saves them."""
    os.makedirs(output_dir, exist_ok=True)
    app = zivid.Application()
    print("Connecting to Zivid camera...")
    camera = app.connect_camera()

    print("Creating default capture settings...")
    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    print("Capturing frame...")
    frame = camera.capture_2d_3d(settings)

    image_file = os.path.join(output_dir, "ImageRGBA.png")
    print(f"Saving 2D color image (sRGB color space) to file: {image_file}")
    frame.frame_2d().image_rgba_srgb().save(image_file)

    zdf_file = os.path.join(output_dir, "Frame.zdf")
    print(f"Saving frame to file: {zdf_file}")
    frame.save(zdf_file)

    ply_file = os.path.join(output_dir, "PointCloud.ply")
    print(f"Exporting point cloud to file: {ply_file}")
    frame.save(ply_file)

    print("Zivid capture complete.")
    return image_file, zdf_file, ply_file