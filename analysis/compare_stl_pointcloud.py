import open3d as o3d
import numpy as np
import pandas as pd

def compare_stl_and_pointcloud(stl_path, ply_path, mesh_points=100000):
    """
    Compares an STL mesh and a measured point cloud (PLY).
    Args:
        stl_path (str): Path to the reference STL file.
        ply_path (str): Path to the measured point cloud (PLY file).
        mesh_points (int): Number of points to sample from the mesh for comparison.
    Returns:
        points_with_distances_df (pd.DataFrame): DataFrame with columns x, y, z, distance.
        stats (dict): Dictionary with min, max, mean distance.
    """
    # Load STL mesh and convert to point cloud
    mesh = o3d.io.read_triangle_mesh(stl_path)
    mesh.compute_vertex_normals()
    mesh_pc = mesh.sample_points_uniformly(number_of_points=mesh_points)

    # Load measured point cloud
    pcd = o3d.io.read_point_cloud(ply_path)

    # Compute distances
    distances = np.asarray(pcd.compute_point_cloud_distance(mesh_pc))
    points = np.asarray(pcd.points)

    # Prepare DataFrame
    points_with_distances_df = pd.DataFrame(
        np.hstack((points, distances.reshape(-1, 1))),
        columns=["x", "y", "z", "distance"]
    )

    # Compute stats
    stats = {
        "min": float(np.min(distances)),
        "max": float(np.max(distances)),
        "mean": float(np.mean(distances))
    }

    return points_with_distances_df, stats