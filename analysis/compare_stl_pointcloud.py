import pandas as pd
import numpy as np
import open3d as o3d
import matplotlib.pyplot as plt
import os

# === PARAMETER FESTLEGEN ===

# Pfad zur Eingabedatei (CSV mit Punktwolke)
file_path = '/Users/jonaskreuziger/Documents/WBK_hackaton/AutomatisierungsCode/Ergebnisse/points_with_distances.csv'

# Pfad zur Ausgabedatei (CSV mit Voxel-Ergebnissen)
output_path = '/Users/jonaskreuziger/Documents/WBK_hackaton/AutomatisierungsCode/Ergebnisse/Auswertungabstaende.csv'

# Größe eines Würfels (Voxel) in allen Raumrichtungen (Einheit z. B. mm, m …)
voxel_size = 0.00005

# Schwelle: Wenn der Mittelwert der Distanz in einem Voxel größer ist, wird das Voxel als "kritisch" markiert
dist_threshold = 0.0005

# Mindestanzahl von Punkten in einem Voxel, damit es überhaupt berücksichtigt wird
min_points_per_voxel = 1

# === Dateipfade anpassen ===
mesh_path = os.path.join(os.path.dirname(__file__), "../data/raw/CAD.stl")
pointcloud_path = os.path.join(os.path.dirname(__file__), "../data/raw/PointCloud.ply")
output_folder = os.path.join(os.path.dirname(__file__), "../data/processed")
os.makedirs(output_folder, exist_ok=True)

# === CSV-DATEI MIT PUNKTWOLKE EINLESEN ===

# Erwartet Spalten: x, y, z (Koordinaten) und Distanz (Messwert)
df = pd.read_csv(file_path)

# Optional: erste Zeilen anzeigen, um zu prüfen, ob Einlesen funktioniert hat
print(df.head())

# === VOXELISIERUNG: Punktkoordinaten in Voxel-Koordinaten umwandeln ===

# Jeder Punkt wird einem Würfel zugeordnet – z. B. bei voxel_size = 1:
# Ein Punkt bei x = 3.7 liegt im Voxel mit Index voxel_x = 3
df['voxel_x'] = np.floor(df['x'] / voxel_size).astype(int)
df['voxel_y'] = np.floor(df['y'] / voxel_size).astype(int)
df['voxel_z'] = np.floor(df['z'] / voxel_size).astype(int)

# === GRUPPIEREN NACH VOXEL ===

# Alle Punkte mit denselben Voxel-Koordinaten werden zu einer Gruppe zusammengefasst
voxel_groups = df.groupby(['voxel_x', 'voxel_y', 'voxel_z'])

# === ERGEBNISLISTE INITIALISIEREN ===

results = []

# Durch alle Voxel-Gruppen gehen
for voxel, points in voxel_groups:
    # Nur Voxel berücksichtigen, die genügend Punkte enthalten
    if len(points) >= min_points_per_voxel:
        # Mittelwert der Distanz in diesem Voxel berechnen
        mean_distance = points['distance'].mean()

        # Prüfen, ob dieser Mittelwert die Schwelle überschreitet
        exceeds_threshold = mean_distance > dist_threshold

        # Ergebnis als Dictionary speichern
        results.append({
            'voxel_x': voxel[0],
            'voxel_y': voxel[1],
            'voxel_z': voxel[2],
            'num_points': len(points),
            'mean_distance': mean_distance,
            'exceeds_threshold': exceeds_threshold
        })

# === ERGEBNIS ALS CSV SPEICHERN ===

# Ergebnisliste in DataFrame umwandeln
results_df = pd.DataFrame(results)

# In CSV-Datei schreiben – ohne Indexspalte
results_df.to_csv(output_path, index=False)

print(f"Ergebnis gespeichert in: {output_path}")

# === 1. STL laden ===
mesh = o3d.io.read_triangle_mesh(mesh_path)
mesh.compute_vertex_normals()

# === 2. In Punktwolke umwandeln ===
mesh_pc = mesh.sample_points_uniformly(number_of_points=100000)

# === 3. Punktwolke laden ===
pcd = o3d.io.read_point_cloud(pointcloud_path)

# === 4. Distanz berechnen ===
distances = np.asarray(pcd.compute_point_cloud_distance(mesh_pc))

# === 5. Statistik berechnen ===
d_min = np.min(distances)
d_max = np.max(distances)
d_mean = np.mean(distances)

# === 6. Ergebnisse speichern: Koordinaten + Distanz ===
points = np.asarray(pcd.points)
data = np.hstack((points, distances.reshape(-1, 1)))  # shape: [n, 4]
header = "x,y,z,distance"
np.savetxt(os.path.join(output_folder, "points_with_distances.csv"), data, delimiter=",", header=header, comments='')

with open(os.path.join(output_folder, "statistik.txt"), "w") as f:
    f.write(f"Min distance: {d_min:.6f} m\n")
    f.write(f"Max distance: {d_max:.6f} m\n")
    f.write(f"Mean distance: {d_mean:.6f} m\n")

# === 7. Visualisierung ===
pcd.colors = o3d.utility.Vector3dVector(
    plt.cm.jet((distances - d_min) / (d_max - d_min))[:, :3]
)
o3d.visualization.draw_geometries([pcd])

# === 2D-Projektion der Punktwolke ===
fig_pc = plt.figure()
ax_pc = fig_pc.add_subplot(111)
sc_pc = ax_pc.scatter(
    points[:, 0],
    points[:, 1],
    c=distances,
    cmap='plasma',
    s=1,
    alpha=0.8
)
cbar_pc = plt.colorbar(sc_pc, ax=ax_pc)
cbar_pc.set_label('Distanz zur STL')
ax_pc.set_xlabel('x-Koordinate')
ax_pc.set_ylabel('y-Koordinate')
plt.title('2D-Projektion der Punktwolke (XY) mit Distanzfärbung')
plt.savefig(os.path.join(output_folder, "pointcloud_projection_2D_XY.png"), dpi=300)
plt.close(fig_pc)

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot der Voxel-Punkte mit Farbskala
sc = ax.scatter(
    results_df['voxel_x'],
    results_df['voxel_y'],
    results_df['voxel_z'],
    c=results_df['mean_distance'],
    cmap='viridis',
    s=40,
    alpha=0.9
)

# Farbleiste und Beschriftung
cbar = plt.colorbar(sc, ax=ax, shrink=0.5, pad=0.1)
cbar.set_label('Mittlerer Distanzwert')

# Achsenbeschriftungen
ax.set_xlabel('Voxel X')
ax.set_ylabel('Voxel Y')
ax.set_zlabel('Voxel Z')

plt.title('Mittlere Distanzwerte pro Voxel (alle Voxel)')

# === Plot speichern ===
plt.savefig('/Users/jonaskreuziger/Documents/WBK_hackaton/AutomatisierungsCode/Ergebnisse/voxel_plot.png', dpi=300)

# Plot anzeigen
plt.show()


def compare_stl_and_pointcloud(stl_path, ply_path):
    """
    Compares an STL mesh and a measured point cloud (PLY).
    Returns:
        points_with_distances_df: pd.DataFrame with columns x, y, z, distance
        stats: dict with min, max, mean distance
    """
    # Load STL mesh and convert to point cloud
    mesh = o3d.io.read_triangle_mesh(stl_path)
    mesh.compute_vertex_normals()
    mesh_pc = mesh.sample_points_uniformly(number_of_points=100000)

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