import numpy as np
import pandas as pd

def voxel_analysis(points_with_distances_df, voxel_size=0.00005, dist_threshold=0.0005, min_points_per_voxel=1):
    """
    Performs voxel-based analysis on a DataFrame with columns x, y, z, distance.
    Returns:
        results_df: pd.DataFrame with voxel_x, voxel_y, voxel_z, num_points, mean_distance, exceeds_threshold
    """
    df = points_with_distances_df.copy()
    df['voxel_x'] = np.floor(df['x'] / voxel_size).astype(int)
    df['voxel_y'] = np.floor(df['y'] / voxel_size).astype(int)
    df['voxel_z'] = np.floor(df['z'] / voxel_size).astype(int)

    voxel_groups = df.groupby(['voxel_x', 'voxel_y', 'voxel_z'])
    results = []
    for voxel, points in voxel_groups:
        if len(points) >= min_points_per_voxel:
            mean_distance = points['distance'].mean()
            exceeds_threshold = mean_distance > dist_threshold
            results.append({
                'voxel_x': voxel[0],
                'voxel_y': voxel[1],
                'voxel_z': voxel[2],
                'num_points': len(points),
                'mean_distance': mean_distance,
                'exceeds_threshold': exceeds_threshold
            })
    results_df = pd.DataFrame(results)
    return results_df