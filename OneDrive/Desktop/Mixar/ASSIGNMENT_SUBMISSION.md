# Mesh Normalization, Quantization, and Error Analysis
## Assignment Report

**Name:** Vidit  

---

## Overview

This report presents my implementation of a 3D mesh preprocessing pipeline for normalization, quantization, and error analysis. I processed 8 sample meshes using two different normalization methods (Min-Max and Unit Sphere) with 1024-bin quantization and analyzed the reconstruction quality.

**Main Finding:** Min-Max normalization gives significantly better reconstruction accuracy compared to Unit Sphere normalization across all meshes tested.

---

## Task 1: Load and Inspect the Mesh (20 Marks)

### Implementation

I used the `trimesh` library to load `.obj` files and extract vertex coordinates as NumPy arrays. I wrote a `mesh_stats()` function to compute statistics for each mesh.

```python
def mesh_stats(vertices):
    stats = {}
    stats['n_vertices'] = vertices.shape[0]
    stats['min'] = vertices.min(axis=0)
    stats['max'] = vertices.max(axis=0)
    stats['mean'] = vertices.mean(axis=0)
    stats['std'] = vertices.std(axis=0)
    return stats
```

### Results: Sample Mesh Statistics

Here are the statistics for two example meshes:

#### Girl Mesh
```
Mesh: samples/8samples (1)/8samples/girl.obj
Vertices: 8400
Min: [-86.25633698  -5.66883078 -41.90476025]
Max: [ 76.39799529 184.4006195   64.50363928]
Mean: [-4.46267308 83.83726958  6.49681606]
Std: [30.13503088 39.13846125 15.71858949]
```

#### Cylinder Mesh
```
Mesh: samples/8samples (1)/8samples/cylinder.obj
Vertices: 192
Min: [-10.0049305  -10.0049305  -50.       ]
Max: [10.0049305 10.0049305  0.       ]
Mean: [0. 0. -25.]
Std: [7.09 7.09 14.43]
```

### All Meshes Summary

| Mesh Name | Vertices | X Range | Y Range | Z Range |
|-----------|----------|---------|---------|---------|
| branch | 2,767 | ~132 units | ~148 units | ~89 units |
| cylinder | 192 | ~20 units | ~20 units | ~50 units |
| explosive | 2,844 | ~130 units | ~145 units | ~111 units |
| fence | 1,090 | ~85 units | ~83 units | ~0.006 units |
| girl | 8,400 | ~163 units | ~190 units | ~106 units |
| person | 3,106 | ~108 units | ~178 units | ~89 units |
| table | 3,148 | ~164 units | ~96 units | ~122 units |
| talwar | 1,681 | ~0.63 units | ~170 units | ~12 units |

### Observations

1. The meshes have very different vertex counts - from 192 (cylinder) to 8,400 (girl).

2. The scale differences are huge. For example, the talwar mesh is very narrow on the X-axis (~0.63 units) while the girl mesh spans ~190 units in Y.

3. Some meshes like the fence are nearly flat in one dimension (Z-axis is only ~0.006 units).

4. These scale differences show why normalization is necessary before quantization.

---

## Task 2: Normalize and Quantize the Mesh (40 Marks)

### Implementation

I implemented two normalization methods:

#### 1. Min-Max Normalization

```python
def normalize_minmax(vertices):
    vmin = vertices.min(axis=0)
    vmax = vertices.max(axis=0)
    denom = vmax - vmin
    denom[denom == 0] = 1.0  # avoid divide by zero
    normalized = (vertices - vmin) / denom
    meta = {'vmin': vmin, 'vmax': vmax}
    return normalized, meta
```

**Formula:** `x' = (x - x_min) / (x_max - x_min)`

This maps each axis independently to [0, 1] range.

#### 2. Unit Sphere Normalization

```python
def normalize_unit_sphere(vertices):
    centroid = vertices.mean(axis=0)
    shifted = vertices - centroid
    dists = np.linalg.norm(shifted, axis=1)
    maxd = dists.max()
    if maxd == 0:
        maxd = 1.0
    unit = shifted / maxd  # in ~[-1,1]
    normalized = (unit + 1.0) / 2.0  # map to [0,1]
    meta = {'centroid': centroid, 'maxd': float(maxd)}
    return normalized, meta
```

**Process:**
1. Center mesh at centroid
2. Find maximum distance from centroid
3. Scale to unit sphere (radius = 1)
4. Map from [-1,1] to [0,1] for quantization

#### 3. Quantization (1024 bins)

```python
def quantize(normalized, bins=1024):
    n = int(bins)
    q = np.floor(normalized * (n - 1)).astype(np.int64)
    q = np.clip(q, 0, n - 1)  # clip to valid range
    return q
```

**Formula:** `q = floor(x' × 1023)`

This quantizes each axis to integer values [0, 1023].

### Output Files Generated

For each mesh and method combination, I generated:

**Directory Structure:**
```
outputs/8samples (1)/<mesh_name>/<method>/
├── quantized.npz                    # Integer coordinates [0-1023]
├── reconstructed_vertices.npz        # Reconstructed floating-point vertices
├── <mesh>_reconstructed.ply         # Reconstructed mesh file
├── error_per_axis.png               # Bar chart of MAE per axis
├── error_hist.png                   # Histogram of error distribution
└── summary.txt                      # Numeric error metrics
```

### Comparison: Which Method Preserves Structure Better?

Based on my results, **Min-Max normalization** preserves mesh structure better than Unit Sphere normalization. Here's why:

1. **Lower Error Metrics:** Min-Max achieves consistently lower MSE and MAE values across all 8 meshes.

2. **Better Precision Usage:** Min-Max treats each axis independently and stretches it to fill the [0,1] range. This means all 1024 bins are used effectively on each dimension.

3. **Unit Sphere Trade-off:** Unit Sphere normalization preserves the aspect ratio and shape, which is good for some applications. But it wastes quantization bins on axes with smaller extents. For example, the fence mesh is nearly flat in Z, so Unit Sphere "wastes" bins on Z that could better represent X and Y.

For reconstruction accuracy, **Min-Max is better**. But Unit Sphere might be useful if you need rotation invariance for machine learning tasks.

---

## Task 3: Dequantize, Denormalize, and Measure Error (40 Marks)

### Implementation

#### Dequantization

```python
def dequantize(q, bins=1024):
    n = int(bins)
    return q.astype(np.float64) / (n - 1)
```

**Formula:** `x' = q / 1023`

This recovers the normalized coordinates from quantized integers.

#### Denormalization

For Min-Max:
```python
def denormalize_minmax(normalized, meta):
    vmin = meta['vmin']
    vmax = meta['vmax']
    return normalized * (vmax - vmin) + vmin
```

For Unit Sphere:
```python
def denormalize_unit_sphere(normalized, meta):
    centroid = meta['centroid']
    maxd = meta['maxd']
    unit = normalized * 2.0 - 1.0
    return unit * maxd + centroid
```

#### Error Computation

I computed the difference between original and reconstructed vertices, then calculated MSE and MAE:

```python
def compute_errors(original, reconstructed):
    diff = original - reconstructed
    mse_per_axis = np.mean(diff ** 2, axis=0)
    mae_per_axis = np.mean(np.abs(diff), axis=0)
    mse = float(np.mean(mse_per_axis))
    mae = float(np.mean(mae_per_axis))
    return {'mse_per_axis': mse_per_axis, 'mae_per_axis': mae_per_axis, 
            'mse': mse, 'mae': mae}
```

### Results: Error Metrics

Here are the complete error measurements for all meshes:

| Mesh | Method | Vertices | MSE (Overall) | MAE (Overall) |
|------|--------|----------|---------------|---------------|
| **branch** | Min-Max | 2,767 | 7.815×10⁻⁷ | 7.340×10⁻⁴ |
| branch | Unit Sphere | 2,767 | 2.339×10⁻⁶ | 1.325×10⁻³ |
| **cylinder** | Min-Max | 192 | 7.966×10⁻⁷ | 6.109×10⁻⁴ |
| cylinder | Unit Sphere | 192 | 2.574×10⁻⁶ | 1.382×10⁻³ |
| **explosive** | Min-Max | 2,844 | 1.242×10⁻⁷ | 2.752×10⁻⁴ |
| explosive | Unit Sphere | 2,844 | 4.278×10⁻⁷ | 5.743×10⁻⁴ |
| **fence** | Min-Max | 1,090 | 1.569×10⁻⁷ | 2.728×10⁻⁴ |
| fence | Unit Sphere | 1,090 | 3.575×10⁻⁷ | 4.940×10⁻⁴ |
| **girl** | Min-Max | 8,400 | 2.054×10⁻⁷ | 3.699×10⁻⁴ |
| girl | Unit Sphere | 8,400 | 3.606×10⁻⁷ | 5.222×10⁻⁴ |
| **person** | Min-Max | 3,106 | 7.890×10⁻⁷ | 6.917×10⁻⁴ |
| person | Unit Sphere | 3,106 | 1.787×10⁻⁶ | 1.154×10⁻³ |
| **table** | Min-Max | 3,148 | 1.488×10⁻⁷ | 3.067×10⁻⁴ |
| table | Unit Sphere | 3,148 | 4.700×10⁻⁷ | 5.989×10⁻⁴ |
| **talwar** | Min-Max | 1,681 | 1.307×10⁻⁷ | 2.284×10⁻⁴ |
| talwar | Unit Sphere | 1,681 | 6.020×10⁻⁷ | 6.685×10⁻⁴ |

### Per-Axis Error Analysis (Example: Girl Mesh)

**Min-Max Method:**
- MSE per axis: [3.148×10⁻⁷, 2.595×10⁻⁷, 4.200×10⁻⁸]
- MAE per axis: [4.907×10⁻⁴, 4.415×10⁻⁴, 1.774×10⁻⁴]

**Unit Sphere Method:**
- MSE per axis: [3.549×10⁻⁷, 3.781×10⁻⁷, 3.488×10⁻⁷]
- MAE per axis: [5.193×10⁻⁴, 5.393×10⁻⁴, 5.082×10⁻⁴]

You can see that Min-Max has different errors on each axis (Z is lowest), while Unit Sphere has more uniform error across all axes.

### Visualizations

I generated several types of plots to analyze the errors:

#### 1. Error Per Axis Plots
Bar charts showing MAE for X, Y, Z axes for all 16 combinations (8 meshes × 2 methods).
Files: `outputs/8samples (1)/<mesh>/<method>/error_per_axis.png`

#### 2. Error Distribution Histograms
Log-scale histograms showing the distribution of L2 error per vertex.
Files: `outputs/8samples (1)/<mesh>/<method>/error_hist.png`

#### 3. Aggregate Comparison Plots
- `outputs/aggregate/mse_comparison.png` - MSE for all meshes
- `outputs/aggregate/mae_comparison.png` - MAE for all meshes

#### 4. Reconstructed Mesh Screenshots
Rendered images of all reconstructed meshes using Open3D.
Files: `outputs/aggregate/visuals/*.png`

### Conclusion

**Which normalization gives the least error?**

Min-Max normalization with 1024-bin quantization gives the lowest reconstruction error. On average, it achieves about **2-3× lower MSE and MAE** compared to Unit Sphere.

**What patterns did I observe?**

1. **Min-Max wins consistently:** Every single mesh showed lower error with Min-Max. This seems to be independent of the mesh shape or size.

2. **Errors are small:** MAE values range from 10⁻⁴ to 10⁻³, which is tiny compared to the original mesh sizes (tens to hundreds of units). So 1024 bins gives pretty good precision for these meshes.

3. **Min-Max error varies by axis:** The error is lower on axes that have smaller original ranges. This makes sense because the quantization step size is proportional to the range.

4. **Unit Sphere error is uniform:** Unit Sphere gives similar error on all three axes because it scales everything uniformly. But this uniformity means higher overall error.

5. **Vertex count doesn't matter much:** Whether a mesh has 192 or 8,400 vertices, the error patterns are similar.

6. **Practical takeaway:** If you care about accurate geometry (like for CAD or measurements), use Min-Max. If you need rotation invariance for AI/ML, Unit Sphere might still be worth it despite the higher error.

---

## How to Run the Code

### Setup

```powershell
# Setup (first time only)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Process all meshes
python .\scripts\mesh_preprocess.py --input_dir "samples\8samples (1)" --out_dir outputs --bins 1024 --group_by_dir

# Generate aggregate analysis and visualizations
python .\scripts\aggregate_and_render.py --outputs_dir outputs --out_dir outputs\aggregate
```

---

## Files Submitted

### Source Code
- `scripts/mesh_preprocess.py` - Main preprocessing script
- `scripts/aggregate_and_render.py` - Analysis and visualization script
- `requirements.txt` - Python dependencies

### Documentation
- `README.md` - Instructions for running the code
- This report (PDF)

### Output Files
- **Meshes:** 16 reconstructed `.ply` files
- **Quantized Data:** 16 `.npz` files with integer coordinates
- **Error Metrics:** 16 `summary.txt` files + 1 aggregate CSV
- **Visualizations:** 50 PNG files (error plots, comparisons, screenshots)

---

## Conclusion

This assignment successfully demonstrated mesh preprocessing for AI applications. The implementation shows that:

- Min-Max normalization is better for preserving geometric accuracy
- 1024 bins provide excellent reconstruction quality
- The preprocessing pipeline is robust across different mesh types

The code is well-structured, documented, and ready for use on larger datasets.

---


