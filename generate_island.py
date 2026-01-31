"""
Procedural Island Generator for Blender

This script creates a low-poly island with:
- Terrain mesh
- House structure
- Trees and rocks
- Dock with boat
- Water plane
- Lighting and camera

SAFE FOR BACKGROUND EXECUTION:
- Uses bpy.data.* APIs (not bpy.ops.*)
- Reports progress via send_status()
- Guaranteed to terminate
- No UI dependencies
"""

import bpy
import random
import math
import bmesh

def main():
    send_status("Starting island generation...")
    
    # Clear existing scene
    send_status("Clearing scene")
    clear_scene()
    
    # Create water
    send_status("Creating water plane")
    create_water()
    
    # Create island terrain
    send_status("Creating island terrain")
    create_island()
    
    # Create house
    send_status("Creating house")
    create_house()
    
    # Create dock
    send_status("Creating dock and boat")
    create_dock()
    
    # Create trees
    send_status("Creating trees")
    create_trees()
    
    # Create rocks
    send_status("Creating rocks")
    create_rocks()
    
    # Setup lighting
    send_status("Setting up lighting")
    create_lighting()
    
    # Setup camera
    send_status("Setting up camera")
    create_camera()
    
    send_status("Island generation complete!")


def clear_scene():
    """Remove all objects from the scene."""
    # Remove all objects
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    
    # Clear orphan data
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)


def create_material(name, color, roughness=0.8):
    """Create a simple material with the given color."""
    # Color can be hex string or tuple
    if isinstance(color, str):
        h = color.lstrip('#')
        r, g, b = tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))
    else:
        r, g, b = color[:3]
    
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (r, g, b, 1.0)
        bsdf.inputs['Roughness'].default_value = roughness
    return mat


def create_mesh_object(name, verts, faces, material=None):
    """Create a mesh object from vertices and faces."""
    mesh = bpy.data.meshes.new(name + "_mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    
    if material:
        obj.data.materials.append(material)
    
    return obj


def create_cube(name, size, location, material=None):
    """Create a cube mesh."""
    s = size / 2
    verts = [
        (-s, -s, -s), (s, -s, -s), (s, s, -s), (-s, s, -s),
        (-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)
    ]
    faces = [
        (0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1),
        (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)
    ]
    
    # Transform vertices
    verts = [(v[0] + location[0], v[1] + location[1], v[2] + location[2]) for v in verts]
    
    return create_mesh_object(name, verts, faces, material)


def create_cylinder(name, radius, height, segments, location, material=None):
    """Create a cylinder mesh."""
    verts = []
    faces = []
    
    # Bottom and top center
    bottom_center = len(verts)
    verts.append((location[0], location[1], location[2] - height/2))
    top_center = len(verts)
    verts.append((location[0], location[1], location[2] + height/2))
    
    # Side vertices
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = location[0] + radius * math.cos(angle)
        y = location[1] + radius * math.sin(angle)
        verts.append((x, y, location[2] - height/2))  # Bottom
        verts.append((x, y, location[2] + height/2))  # Top
    
    # Bottom face
    bottom_face = [bottom_center]
    for i in range(segments):
        bottom_face.append(2 + i * 2)
    faces.append(tuple(reversed(bottom_face)))
    
    # Top face
    top_face = [top_center]
    for i in range(segments):
        top_face.append(3 + i * 2)
    faces.append(tuple(top_face))
    
    # Side faces
    for i in range(segments):
        next_i = (i + 1) % segments
        bl = 2 + i * 2
        br = 2 + next_i * 2
        tl = 3 + i * 2
        tr = 3 + next_i * 2
        faces.append((bl, br, tr, tl))
    
    return create_mesh_object(name, verts, faces, material)


def create_water():
    """Create water plane."""
    mat = create_material("Water", "#4A90D9", roughness=0.1)
    
    size = 50
    verts = [(-size, -size, -0.5), (size, -size, -0.5), (size, size, -0.5), (-size, size, -0.5)]
    faces = [(0, 1, 2, 3)]
    
    create_mesh_object("Water", verts, faces, mat)


def create_island():
    """Create the island terrain using a deformed grid."""
    mat = create_material("Sand", "#E8D4A8", roughness=0.9)
    
    subdivisions = 30
    size = 12
    
    verts = []
    faces = []
    
    # Create grid vertices with height variation
    for y in range(subdivisions):
        for x in range(subdivisions):
            # Position normalized to -1 to 1
            nx = (x / (subdivisions - 1)) * 2 - 1
            ny = (y / (subdivisions - 1)) * 2 - 1
            
            # Distance from center
            dist = math.sqrt(nx*nx + ny*ny)
            
            # Height falloff from center
            height = max(0, 1 - dist) * 2
            height += random.uniform(-0.1, 0.1)
            
            # Clamp to island shape
            if dist > 0.9:
                height = max(-0.3, height - (dist - 0.9) * 5)
            
            px = nx * size
            py = ny * size
            pz = height
            
            verts.append((px, py, pz))
    
    # Create faces
    for y in range(subdivisions - 1):
        for x in range(subdivisions - 1):
            i = y * subdivisions + x
            faces.append((i, i + 1, i + subdivisions + 1, i + subdivisions))
    
    create_mesh_object("Island", verts, faces, mat)


def create_house():
    """Create the house structure."""
    mat_wall = create_material("Wall", "#DEB887", roughness=0.9)
    mat_roof = create_material("Roof", "#8B4513", roughness=0.8)
    mat_wood = create_material("Wood", "#654321", roughness=0.85)
    
    # Main building floor 1
    create_cube("House_Floor1", 3, (2, 2, 1.5), mat_wall)
    
    # Main building floor 2
    create_cube("House_Floor2", 2.5, (2, 2, 3.5), mat_wall)
    
    # Roof (simple pyramid approximation with a box for now)
    create_cube("Roof", 3.5, (2, 2, 5), mat_roof)
    
    # Deck
    verts = [(-1, 0, 0.8), (3, 0, 0.8), (3, 4, 0.8), (-1, 4, 0.8),
             (-1, 0, 0.9), (3, 0, 0.9), (3, 4, 0.9), (-1, 4, 0.9)]
    faces = [(0,1,2,3), (4,7,6,5), (0,4,5,1), (1,5,6,2), (2,6,7,3), (3,7,4,0)]
    create_mesh_object("Deck", verts, faces, mat_wood)
    
    # Deck posts
    for x, y in [(-0.5, 0.5), (-0.5, 3.5), (2.5, 0.5), (2.5, 3.5)]:
        create_cylinder(f"Post_{x}_{y}", 0.1, 1.5, 8, (x, y, 0.4), mat_wood)


def create_dock():
    """Create dock and boat."""
    mat_wood = create_material("DockWood", "#8B7355", roughness=0.9)
    mat_boat = create_material("Boat", "#CD853F", roughness=0.8)
    
    # Dock planks
    for i in range(8):
        x = -4 - i * 0.8
        create_cube(f"Plank_{i}", 0.7, (x, -3, 0.3), mat_wood)
    
    # Dock posts
    for i in range(3):
        x = -4 - i * 2.5
        create_cylinder(f"DockPost_{i}_L", 0.12, 2, 8, (x, -2.5, -0.3), mat_wood)
        create_cylinder(f"DockPost_{i}_R", 0.12, 2, 8, (x, -3.5, -0.3), mat_wood)
    
    # Boat (simple hull)
    verts = [
        (-10, -2.5, 0), (-10, -3.5, 0), (-11, -3, 0),  # Back
        (-10, -2.5, 0.5), (-10, -3.5, 0.5), (-11.5, -3, 0.3),  # Front
    ]
    faces = [(0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5), (3, 4, 5), (0, 2, 1)]
    create_mesh_object("Boat", verts, faces, mat_boat)


def create_trees():
    """Create low-poly trees."""
    mat_trunk = create_material("Trunk", "#4A3728", roughness=0.9)
    mat_leaves = create_material("Leaves", "#228B22", roughness=0.8)
    
    tree_positions = [(-5, 4, 0.5), (5, 3, 0.3), (-3, -5, 0.2), (4, -4, 0.4), (6, 1, 0.3)]
    
    for i, (x, y, z) in enumerate(tree_positions):
        # Trunk
        create_cylinder(f"Trunk_{i}", 0.2, 2, 6, (x, y, z + 1), mat_trunk)
        
        # Foliage (stacked spheres approximated with icospheres - using cubes for simplicity)
        for j, h in enumerate([1.5, 2.2, 2.8]):
            size = 1.5 - j * 0.3
            create_cube(f"Foliage_{i}_{j}", size, (x, y, z + h + 0.5), mat_leaves)


def create_rocks():
    """Create simple rock meshes."""
    mat_rock = create_material("Rock", "#696969", roughness=0.95)
    
    rock_positions = [(6, -2, 0.3), (5, 5, 0.2), (-6, -3, 0.25), (7, 2, 0.15)]
    
    for i, (x, y, z) in enumerate(rock_positions):
        size = 0.5 + random.random() * 0.5
        create_cube(f"Rock_{i}", size, (x, y, z), mat_rock)


def create_lighting():
    """Set up scene lighting."""
    # Sun light
    sun_data = bpy.data.lights.new(name="Sun", type='SUN')
    sun_data.energy = 3.0
    sun_obj = bpy.data.objects.new("Sun", sun_data)
    sun_obj.location = (10, -10, 15)
    sun_obj.rotation_euler = (0.8, 0.2, 0.5)
    bpy.context.collection.objects.link(sun_obj)
    
    # Fill light
    fill_data = bpy.data.lights.new(name="Fill", type='AREA')
    fill_data.energy = 200
    fill_obj = bpy.data.objects.new("Fill", fill_data)
    fill_obj.location = (-8, -8, 8)
    bpy.context.collection.objects.link(fill_obj)


def create_camera():
    """Set up the camera."""
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", cam_data)
    cam_obj.location = (20, -20, 15)
    cam_obj.rotation_euler = (1.1, 0, 0.78)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj


# Run the main function
main()
