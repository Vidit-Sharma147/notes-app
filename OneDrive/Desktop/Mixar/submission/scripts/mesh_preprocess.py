"""
Mesh normalization, quantization, reconstruction, and error analysis.

Usage:
    python scripts/mesh_preprocess.py --input_dir samples --out_dir outputs --bins 1024

This script will:
 - find .obj files under the input directory
 - for each mesh, load vertices (and faces if present)
 - apply two normalizations: min-max and unit-sphere
 - quantize (bins default 1024), dequantize, denormalize
 - compute MSE and MAE per axis and overall
 - save reconstructed meshes and plots under outputs/<meshname>/<method>/

Dependencies: trimesh, numpy, matplotlib
"""
import os
import argparse
import glob
import traceback

import numpy as np
import trimesh
import matplotlib.pyplot as plt


def find_obj_files(input_dir):
    pattern = os.path.join(input_dir, '**', '*.obj')
    return glob.glob(pattern, recursive=True)


def mesh_stats(vertices):
    stats = {}
    stats['n_vertices'] = vertices.shape[0]
    stats['min'] = vertices.min(axis=0)
    stats['max'] = vertices.max(axis=0)
    stats['mean'] = vertices.mean(axis=0)
    stats['std'] = vertices.std(axis=0)
    return stats


def normalize_minmax(vertices):
    vmin = vertices.min(axis=0)
    vmax = vertices.max(axis=0)
    denom = vmax - vmin
    # avoid divide by zero
    denom[denom == 0] = 1.0
    normalized = (vertices - vmin) / denom
    meta = {'vmin': vmin, 'vmax': vmax}
    return normalized, meta


def denormalize_minmax(normalized, meta):
    vmin = meta['vmin']
    vmax = meta['vmax']
    return normalized * (vmax - vmin) + vmin


def normalize_unit_sphere(vertices):
    centroid = vertices.mean(axis=0)
    shifted = vertices - centroid
    dists = np.linalg.norm(shifted, axis=1)
    maxd = dists.max()
    if maxd == 0:
        maxd = 1.0
    unit = shifted / maxd  # in ~[-1,1]
    # map to [0,1] for quantization convenience
    normalized = (unit + 1.0) / 2.0
    meta = {'centroid': centroid, 'maxd': float(maxd)}
    return normalized, meta


def denormalize_unit_sphere(normalized, meta):
    centroid = meta['centroid']
    maxd = meta['maxd']
    unit = normalized * 2.0 - 1.0
    return unit * maxd + centroid


def quantize(normalized, bins=1024):
    n = int(bins)
    q = np.floor(normalized * (n - 1)).astype(np.int64)
    # clip just in case of numerical issues
    q = np.clip(q, 0, n - 1)
    return q


def dequantize(q, bins=1024):
    n = int(bins)
    return q.astype(np.float64) / (n - 1)


def compute_errors(original, reconstructed):
    diff = original - reconstructed
    mse_per_axis = np.mean(diff ** 2, axis=0)
    mae_per_axis = np.mean(np.abs(diff), axis=0)
    mse = float(np.mean(mse_per_axis))
    mae = float(np.mean(mae_per_axis))
    return {'mse_per_axis': mse_per_axis, 'mae_per_axis': mae_per_axis, 'mse': mse, 'mae': mae}


def save_mesh(vertices, faces, out_path):
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    mesh.export(out_path)


def process_mesh(path, out_dir, bins=1024, visualize=False):
    name = os.path.splitext(os.path.basename(path))[0]
    mesh = trimesh.load(path, process=False)
    if mesh.is_empty:
        print(f"Skipping empty mesh: {path}")
        return
    vertices = np.asarray(mesh.vertices, dtype=np.float64)
    faces = None
    if hasattr(mesh, 'faces'):
        faces = np.asarray(mesh.faces)

    stats = mesh_stats(vertices)
    print(f"\nMesh: {path}")
    print(f"Vertices: {stats['n_vertices']}")
    print(f"Min: {stats['min']}")
    print(f"Max: {stats['max']}")
    print(f"Mean: {stats['mean']}")
    print(f"Std: {stats['std']}")

    methods = [
        ('minmax', normalize_minmax, denormalize_minmax),
        ('unit_sphere', normalize_unit_sphere, denormalize_unit_sphere)
    ]

    for method_name, normalize_fn, denormalize_fn in methods:
        try:
            normalized, meta = normalize_fn(vertices)
            quant = quantize(normalized, bins=bins)
            # save quantized integers
            method_out = os.path.join(out_dir, name, method_name)
            os.makedirs(method_out, exist_ok=True)
            np.savez_compressed(os.path.join(method_out, 'quantized.npz'), quant=quant)

            # dequantize and denormalize
            deq = dequantize(quant, bins=bins)
            recon = denormalize_fn(deq, meta)

            # compute errors
            errors = compute_errors(vertices, recon)
            print(f"Method: {method_name} | MSE: {errors['mse']:.6e} | MAE: {errors['mae']:.6e}")
            print(f"MSE per axis: {errors['mse_per_axis']}")
            print(f"MAE per axis: {errors['mae_per_axis']}")

            # save reconstructed mesh
            recon_path = os.path.join(method_out, f"{name}_reconstructed.ply")
            if faces is not None and faces.size > 0:
                save_mesh(recon, faces, recon_path)
            else:
                # save as point cloud
                pcl = trimesh.PointCloud(recon)
                pcl.export(recon_path)

            # save a numpy file of recon vertices
            np.savez_compressed(os.path.join(method_out, 'reconstructed_vertices.npz'), reconstructed=recon)

            # plot error per axis
            abs_err = np.abs(vertices - recon)
            mean_axis_err = abs_err.mean(axis=0)
            fig, ax = plt.subplots(figsize=(6,4))
            axis_names = ['x', 'y', 'z']
            ax.bar(axis_names, mean_axis_err)
            ax.set_title(f"Mean absolute reconstruction error per axis\n{os.path.basename(path)} - {method_name}")
            ax.set_ylabel('Mean absolute error')
            plt.tight_layout()
            plot_path = os.path.join(method_out, 'error_per_axis.png')
            fig.savefig(plot_path)
            plt.close(fig)

            # optionally save a scatter of original vs reconstructed norms (not mandatory)
            # save a basic histogram of error magnitude
            mag_err = np.linalg.norm(abs_err, axis=1)
            fig, ax = plt.subplots(figsize=(6,4))
            ax.hist(mag_err, bins=100)
            ax.set_yscale('log')
            ax.set_title(f"Error magnitude histogram\n{os.path.basename(path)} - {method_name}")
            ax.set_xlabel('L2 error per vertex')
            ax.set_ylabel('Count (log)')
            plt.tight_layout()
            hist_path = os.path.join(method_out, 'error_hist.png')
            fig.savefig(hist_path)
            plt.close(fig)

            # write a small JSON/text summary
            summary_path = os.path.join(method_out, 'summary.txt')
            with open(summary_path, 'w') as f:
                f.write(f"mesh: {path}\n")
                f.write(f"method: {method_name}\n")
                f.write(f"n_vertices: {stats['n_vertices']}\n")
                f.write(f"bins: {bins}\n")
                f.write(f"MSE: {errors['mse']:.12e}\n")
                f.write(f"MAE: {errors['mae']:.12e}\n")
                f.write(f"MSE_per_axis: {errors['mse_per_axis'].tolist()}\n")
                f.write(f"MAE_per_axis: {errors['mae_per_axis'].tolist()}\n")
                f.write(f"meta: {meta}\n")

        except Exception as e:
            print(f"Error processing {path} with method {method_name}: {e}")
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description='Mesh normalization, quantization, reconstruction, error analysis')
    parser.add_argument('--input_dir', type=str, default='samples', help='Directory with .obj meshes')
    parser.add_argument('--out_dir', type=str, default='outputs', help='Where to store outputs')
    parser.add_argument('--group_by_dir', action='store_true', help='Process each immediate subdirectory of input_dir separately')
    parser.add_argument('--sample', type=str, default=None, help='Path to a single sample (file or directory) to process. If a directory is given it will process .obj files inside it.')
    parser.add_argument('--out_template', type=str, default='{out_dir}/{group}/{name}',
                        help="Output path template. Available keys: out_dir, group, name. Example: '{out_dir}/{group}/{name}'")
    parser.add_argument('--bins', type=int, default=1024, help='Quantization bins')
    args = parser.parse_args()

    def build_out_from_template(out_dir, group, name):
        return args.out_template.format(out_dir=out_dir, group=group, name=name)

    if args.sample:
        # User requested a single sample (file or directory)
        sample_path = args.sample
        # if relative, make relative to input_dir
        if not os.path.isabs(sample_path):
            sample_path = os.path.join(args.input_dir, sample_path)

        if os.path.isfile(sample_path):
            # single file
            name = os.path.splitext(os.path.basename(sample_path))[0]
            group = os.path.basename(os.path.dirname(sample_path)) or 'root'
            out_base = build_out_from_template(args.out_dir, group, name)
            print(f"Processing single file: {sample_path} -> outputs: {out_base}")
            os.makedirs(out_base, exist_ok=True)
            process_mesh(sample_path, out_base, bins=args.bins)
            return
        elif os.path.isdir(sample_path):
            # treat as group directory
            sd = sample_path
            sd_name = os.path.basename(sd)
            sd_obj_files = find_obj_files(sd)
            if not sd_obj_files:
                print(f"No .obj files found under sample directory {sd}. Nothing to do.")
                return
            print(f"Processing sample directory: {sd} with {len(sd_obj_files)} .obj files")
            for p in sd_obj_files:
                name = os.path.splitext(os.path.basename(p))[0]
                out_base = build_out_from_template(args.out_dir, sd_name, name)
                os.makedirs(out_base, exist_ok=True)
                process_mesh(p, out_base, bins=args.bins)
            return
        else:
            # maybe user gave a subdir name under input_dir
            candidate = os.path.join(args.input_dir, args.sample)
            if os.path.isdir(candidate):
                sd = candidate
                sd_name = os.path.basename(sd)
                sd_obj_files = find_obj_files(sd)
                if not sd_obj_files:
                    print(f"No .obj files found under sample directory {sd}. Nothing to do.")
                    return
                print(f"Processing sample directory: {sd} with {len(sd_obj_files)} .obj files")
                for p in sd_obj_files:
                    name = os.path.splitext(os.path.basename(p))[0]
                    out_base = build_out_from_template(args.out_dir, sd_name, name)
                    os.makedirs(out_base, exist_ok=True)
                    process_mesh(p, out_base, bins=args.bins)
                return
            else:
                print(f"Sample path not found: {args.sample}")
                return

    if args.group_by_dir:
        # process each immediate subdirectory separately
        subdirs = [os.path.join(args.input_dir, d) for d in os.listdir(args.input_dir) if os.path.isdir(os.path.join(args.input_dir, d))]
        if not subdirs:
            print(f"No subdirectories found under {args.input_dir} to group by. Falling back to scanning for .obj files.")
            obj_files = find_obj_files(args.input_dir)
            if not obj_files:
                print(f"No .obj files found under {args.input_dir}")
                return
            print(f"Found {len(obj_files)} .obj files.\nProcessing with {args.bins} bins...")
            for p in obj_files:
                process_mesh(p, args.out_dir, bins=args.bins)
        else:
            print(f"Found {len(subdirs)} subdirectories under {args.input_dir}. Processing each separately...")
            for sd in subdirs:
                sd_name = os.path.basename(sd)
                sd_obj_files = find_obj_files(sd)
                if not sd_obj_files:
                    print(f"No .obj files found under subdirectory {sd}. Skipping.")
                    continue
                sd_out = os.path.join(args.out_dir, sd_name)
                print(f"\nProcessing group: {sd_name} with {len(sd_obj_files)} .obj files -> outputs: {sd_out}")
                for p in sd_obj_files:
                    process_mesh(p, sd_out, bins=args.bins)
    else:
        obj_files = find_obj_files(args.input_dir)
        if not obj_files:
            print(f"No .obj files found under {args.input_dir}")
            return

        print(f"Found {len(obj_files)} .obj files.\nProcessing with {args.bins} bins...")
        for p in obj_files:
            process_mesh(p, args.out_dir, bins=args.bins)

    print('\nProcessing complete. Check the outputs/ folder for results.')


if __name__ == '__main__':
    main()
