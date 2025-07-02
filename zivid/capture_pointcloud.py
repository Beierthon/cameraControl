import zivid
import os

def main():
    output_dir = os.path.join(os.path.dirname(__file__), "../data/raw")
    os.makedirs(output_dir, exist_ok=True)

    app = zivid.Application()
    print("Connecting to camera...")
    camera = app.connect_camera()

    print("Creating default capture settings...")
    settings = zivid.Settings(
        acquisitions=[zivid.Settings.Acquisition()],
        color=zivid.Settings2D(acquisitions=[zivid.Settings2D.Acquisition()]),
    )

    print("Capturing frame...")
    frame = camera.capture_2d_3d(settings)

    # Save 2D color image
    image_file = os.path.join(output_dir, "ImageRGBA.png")
    print(f"Saving 2D color image (sRGB color space) to file: {image_file}")
    frame.frame_2d().image_rgba_srgb().save(image_file)

    # Optionally save ZDF (comment out if not needed)
    zdf_file = os.path.join(output_dir, "Frame.zdf")
    # print(f"Saving frame to file: {zdf_file}")
    # frame.save(zdf_file)

    # Save point cloud as PLY
    ply_file = os.path.join(output_dir, "PointCloud.ply")
    print(f"Exporting point cloud to file: {ply_file}")
    frame.save(ply_file)

    print("Zivid capture complete.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error during Zivid capture: {e}") 