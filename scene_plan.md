# Scene Generation Plan

## Goal
Recreate the provided low-poly island image in Blender using Python.

## Components

### 1. Landscape (Island)
- **Mesh**: Cylinder or Cube modified with subdivision and displacement, or just a custom NGon/Curve extruded.
- **Material**: Sand/Beige #E6D690.

### 2. Water
- **Mesh**: Large Plane below the island.
- **Material**: Blue #5F9EA0 (approx).

### 3. House
- **Structure**:
  - Main Body: Cube, scaled (Wood texture/color #C19A6B).
  - Roof: Primtive triangular prism or rotated cube (Roof color #A52A2A).
  - Details: Windows (inset faces), Door.
- **Deck/Pergola**:
  - Wooden posts (Cylinders or thin Cubes).
  - Beams overhead.

### 4. Dock & Boat
- **Dock**: Series of planks (Array modifier on a Cube) and supports.
- **Boat**: Low poly canoe shape (scaled Cube/Sphere).

### 5. Nature
- **Trees**: Cylindrical trunk + Ico Sphere leaves (Green #228B22).
- **Rocks**: Ico Spheres with random displacement (Grey #808080).
- **Fence**: Small cylinders/cubes.

## Execution Strategy
I will write a script `scene_builder.py` that:
1. Clears existing objects.
2. Defines helper functions for creating materials and primitives.
3. Builds each component step-by-step.
4. Sets up a camera and lighting to match the reference.

Then I will use a driver script to send this code to the Blender addon.
