"""
Aggregate summary.txt files into a CSV, create comparative MSE/MAE plots, and render reconstructed meshes to PNG screenshots using Open3D.

Usage:
    python scripts/aggregate_and_render.py --outputs_dir outputs --out_dir outputs/aggregate

Outputs:
 - CSV: aggregate_summary.csv
 - Plots: mse_mae_comparison.png
 - Visuals: visuals/<group>_<mesh>_<method>.png
"""
import os
import argparse
import csv
import glob
import re
import json

import numpy as np
import matplotlib.pyplot as plt

try:
    import open3d as o3d
    O3D_AVAILABLE = True
except Exception:
    O3D_AVAILABLE = False


def parse_summary(path):
    data = {}
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if ':' not in line:
                continue
            k, v = line.split(':', 1)
            k = k.strip()
            v = v.strip()
            # try to parse numbers
            if k in ('MSE', 'MAE'):
                try:
                    data[k.lower()] = float(v)
                except:
                    data[k.lower()] = v
            elif k in ('MSE_per_axis', 'MAE_per_axis'):
                try:
                    arr = json.loads(v.replace("'", '"'))
                    data[k.lower()] = arr
                except:
                    # fallback parse
                    nums = re.findall(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", v)
                    data[k.lower()] = [float(x) for x in nums]
            elif k == 'n_vertices':
                data['n_vertices'] = int(v)
            elif k == 'method':
                data['method'] = v
            elif k == 'mesh':
                data['mesh'] = v
            elif k == 'meta':
                data['meta'] = v
            else:
                # store generically
                data[k.lower()] = v
    return data


def render_mesh_to_image(mesh_path, out_path, width=1024, height=768):
    if not O3D_AVAILABLE:
        print('Open3D not available, skipping rendering for', mesh_path)
        return False
    try:
        mesh = o3d.io.read_triangle_mesh(mesh_path)
        if mesh.is_empty():
            # try point cloud
            pcd = o3d.io.read_point_cloud(mesh_path)
            if pcd.is_empty():
                print('Empty geometry:', mesh_path)
                return False
            geom = pcd
        else:
            geom = mesh
            if not geom.has_vertex_normals():
                geom.compute_vertex_normals()

        vis = o3d.visualization.Visualizer()
        vis.create_window(width=width, height=height, visible=False)
        vis.add_geometry(geom)
        vis.get_render_option().background_color = np.array([1,1,1])
        vis.get_render_option().mesh_show_back_face = True
        vis.poll_events()
        vis.update_renderer()

        # try to set view to fit geometry
        try:
            bbox = geom.get_axis_aligned_bounding_box()
            center = bbox.get_center()
            extent = bbox.get_extent()
            ctr = vis.get_view_control()
            ctr.set_lookat(center)
            # set camera distance
            dist = np.linalg.norm(extent) * 2.0 if np.linalg.norm(extent) > 0 else 1.0
            ctr.set_front([0.0, 0.0, -1.0])
            ctr.set_up([0.0, 1.0, 0.0])
            ctr.set_zoom(0.7)
        except Exception:
            pass

        vis.poll_events()
        vis.update_renderer()
        # capture
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        vis.capture_screen_image(out_path)
        vis.destroy_window()
        return True
    except Exception as e:
        print('Error rendering', mesh_path, e)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--outputs_dir', type=str, default='outputs', help='Directory where per-mesh outputs are stored')
    parser.add_argument('--out_dir', type=str, default='outputs/aggregate', help='Directory to write aggregated outputs')
    args = parser.parse_args()

    files = glob.glob(os.path.join(args.outputs_dir, '**', 'summary.txt'), recursive=True)
    if not files:
        print('No summary.txt files found under', args.outputs_dir)
        return

    rows = []
    for p in files:
        # infer group and mesh and method from path: outputs/.../<mesh>/<method>/summary.txt
        rel = os.path.relpath(p, args.outputs_dir)
        parts = rel.split(os.sep)
        # find method as last parent
        if len(parts) >= 3:
            method = parts[-2]
            mesh = parts[-3]
            group = parts[0]
        elif len(parts) == 2:
            # outputs/<mesh>/summary.txt
            method = ''
            mesh = parts[-2]
            group = parts[0]
        else:
            method = ''
            mesh = os.path.splitext(os.path.basename(p))[0]
            group = ''
        data = parse_summary(p)
        row = {
            'group': group,
            'mesh': mesh,
            'method': data.get('method', method),
            'n_vertices': data.get('n_vertices', ''),
            'mse': data.get('mse', ''),
            'mae': data.get('mae', ''),
            'mse_x': data.get('mse_per_axis', [None, None, None])[0],
            'mse_y': data.get('mse_per_axis', [None, None, None])[1],
            'mse_z': data.get('mse_per_axis', [None, None, None])[2],
            'mae_x': data.get('mae_per_axis', [None, None, None])[0],
            'mae_y': data.get('mae_per_axis', [None, None, None])[1],
            'mae_z': data.get('mae_per_axis', [None, None, None])[2]
        }
        rows.append((p, row))

    os.makedirs(args.out_dir, exist_ok=True)
    csv_path = os.path.join(args.out_dir, 'aggregate_summary.csv')
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['group','mesh','method','n_vertices','mse','mae','mse_x','mse_y','mse_z','mae_x','mae_y','mae_z']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for p, r in rows:
            writer.writerow(r)

    print('Wrote aggregate CSV to', csv_path)

    # create comparative plots: MSE and MAE per mesh for each method
    # group by mesh and method
    import pandas as pd
    df = pd.read_csv(csv_path)
    # pivot
    try:
        mse_pivot = df.pivot(index='mesh', columns='method', values='mse')
        mae_pivot = df.pivot(index='mesh', columns='method', values='mae')
    except Exception as e:
        print('Pivot failed:', e)
        return

    # sort meshes alphabetically
    meshes = mse_pivot.index.tolist()
    x = np.arange(len(meshes))
    methods = mse_pivot.columns.tolist()
    width = 0.35

    fig, ax = plt.subplots(figsize=(12,6))
    for i, method in enumerate(methods):
        vals = mse_pivot[method].values
        ax.bar(x + i*width, vals, width, label=method)
    ax.set_xticks(x + width*(len(methods)-1)/2)
    ax.set_xticklabels(meshes, rotation=45, ha='right')
    ax.set_ylabel('MSE')
    ax.set_title('MSE per mesh by normalization method')
    ax.legend()
    plt.tight_layout()
    mse_plot = os.path.join(args.out_dir, 'mse_comparison.png')
    fig.savefig(mse_plot)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12,6))
    for i, method in enumerate(methods):
        vals = mae_pivot[method].values
        ax.bar(x + i*width, vals, width, label=method)
    ax.set_xticks(x + width*(len(methods)-1)/2)
    ax.set_xticklabels(meshes, rotation=45, ha='right')
    ax.set_ylabel('MAE')
    ax.set_title('MAE per mesh by normalization method')
    ax.legend()
    plt.tight_layout()
    mae_plot = os.path.join(args.out_dir, 'mae_comparison.png')
    fig.savefig(mae_plot)
    plt.close(fig)

    print('Saved comparison plots:', mse_plot, mae_plot)

    # Render reconstructed meshes to PNG
    visuals_dir = os.path.join(args.out_dir, 'visuals')
    os.makedirs(visuals_dir, exist_ok=True)
    for p, r in rows:
        # reconstructed mesh is expected near the summary file path; find *_reconstructed.ply
        summary_dir = os.path.dirname(p)
        cand = glob.glob(os.path.join(summary_dir, '*reconstructed.*'))
        if not cand:
            # maybe parent contains
            cand = glob.glob(os.path.join(summary_dir, '..', '*reconstructed.*'))
        for mesh_file in cand:
            ext = os.path.splitext(mesh_file)[1].lower()
            img_name = f"{r['group']}_{r['mesh']}_{r['method']}{ext}.png".replace(' ', '_')
            out_img = os.path.join(visuals_dir, img_name)
            success = render_mesh_to_image(mesh_file, out_img)
            if success:
                print('Rendered', mesh_file, '->', out_img)

    print('Aggregation and rendering complete.')

if __name__ == '__main__':
    main()
