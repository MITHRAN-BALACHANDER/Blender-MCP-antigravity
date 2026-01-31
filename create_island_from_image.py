"""
Low-Poly Island Scene - Proper Organic Island Shape
"""

import bpy
import random
import math

def main():
    send_status("Creating island scene...")
    
    # Clear scene
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for cam in list(bpy.data.cameras):
        bpy.data.cameras.remove(cam)
    for light in list(bpy.data.lights):
        bpy.data.lights.remove(light)
    
    def mat(name, hex_color, rough=0.5):
        h = hex_color.lstrip('#')
        r, g, b = tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))
        m = bpy.data.materials.new(name=name)
        m.use_nodes = True
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (r, g, b, 1.0)
            bsdf.inputs["Roughness"].default_value = rough
        return m
    
    M_WATER = mat("Water", "#3A7D8C", 0.2)
    M_SAND = mat("Sand", "#D4C4A0", 0.9)
    M_WALL = mat("Wall", "#C9A67A", 0.7)
    M_ROOF = mat("Roof", "#7B3F13", 0.6)
    M_WOOD = mat("Wood", "#5B3413", 0.8)
    M_DECK = mat("Deck", "#B89060", 0.7)
    M_LEAF = mat("Leaf", "#4A6E4A", 0.7)
    M_LEAF2 = mat("Leaf2", "#5A8A5A", 0.7)
    M_TRUNK = mat("Trunk", "#3A2510", 0.9)
    M_ROCK = mat("Rock", "#606060", 0.95)
    M_DOCK = mat("Dock", "#4C2A11", 0.85)
    
    def mesh_obj(name, verts, faces, material):
        m = bpy.data.meshes.new(name)
        m.from_pydata(verts, [], faces)
        m.update()
        obj = bpy.data.objects.new(name, m)
        bpy.context.collection.objects.link(obj)
        if material:
            obj.data.materials.append(material)
        return obj
    
    def box(name, sx, sy, sz, x, y, z, material):
        hx, hy = sx/2, sy/2
        v = [(x-hx,y-hy,z), (x+hx,y-hy,z), (x+hx,y+hy,z), (x-hx,y+hy,z),
             (x-hx,y-hy,z+sz), (x+hx,y-hy,z+sz), (x+hx,y+hy,z+sz), (x-hx,y+hy,z+sz)]
        f = [(0,1,2,3), (4,7,6,5), (0,4,5,1), (1,5,6,2), (2,6,7,3), (3,7,4,0)]
        return mesh_obj(name, v, f, material)
    
    def cyl(name, r, h, segs, x, y, z, material):
        v = [(x, y, z), (x, y, z+h)]
        for i in range(segs):
            a = 2 * math.pi * i / segs
            v.append((x + r * math.cos(a), y + r * math.sin(a), z))
            v.append((x + r * math.cos(a), y + r * math.sin(a), z + h))
        f = []
        f.append(tuple(reversed([0] + [2 + i*2 for i in range(segs)])))
        f.append(tuple([1] + [3 + i*2 for i in range(segs)]))
        for i in range(segs):
            ni = (i + 1) % segs
            f.append((2+i*2, 2+ni*2, 3+ni*2, 3+i*2))
        return mesh_obj(name, v, f, material)
    
    # ===== WATER (large plane below island) =====
    send_status("Creating water...")
    mesh_obj("Water", [(-50,-50,0.05),(50,-50,0.05),(50,50,0.05),(-50,50,0.05)], [(0,1,2,3)], M_WATER)
    
    # ===== CIRCULAR ORGANIC ISLAND =====
    send_status("Creating island...")
    verts, faces = [], []
    random.seed(42)
    
    # Create a circular disc with organic edges
    rings = 15  # Number of concentric rings
    segments = 24  # Points per ring
    
    # Center vertex
    verts.append((0, 0, 1.0))  # Center is highest
    
    for ring in range(1, rings + 1):
        ring_radius = (ring / rings)  # 0 to 1
        actual_radius = ring_radius * 8.5  # Actual world size
        
        for seg in range(segments):
            angle = (seg / segments) * 2 * math.pi
            
            # Add organic edge variation
            edge_noise = 0.12 * math.sin(angle * 5 + 0.3) + 0.08 * math.sin(angle * 8)
            adjusted_radius = actual_radius * (1 + edge_noise * (ring_radius ** 0.5))
            
            x = adjusted_radius * math.cos(angle)
            y = adjusted_radius * math.sin(angle)
            
            # Height - smooth falloff from center, drops below water at edge
            if ring_radius < 0.7:
                h = (1 - ring_radius / 0.7) * 0.9 + 0.2
            elif ring_radius < 0.85:
                h = 0.2 * (0.85 - ring_radius) / 0.15 + 0.05
            else:
                h = 0.05 * (1 - (ring_radius - 0.85) / 0.15)  # Gentle slope to edge
            
            h += random.uniform(-0.02, 0.02)
            verts.append((x, y, max(0.03, h)))
    
    # Create faces - center fan
    for seg in range(segments):
        next_seg = (seg + 1) % segments
        faces.append((0, 1 + seg, 1 + next_seg))
    
    # Create faces - rings
    for ring in range(1, rings):
        ring_start = 1 + (ring - 1) * segments
        next_ring_start = 1 + ring * segments
        
        for seg in range(segments):
            next_seg = (seg + 1) % segments
            v1 = ring_start + seg
            v2 = ring_start + next_seg
            v3 = next_ring_start + next_seg
            v4 = next_ring_start + seg
            faces.append((v1, v2, v3, v4))
    
    mesh_obj("Island", verts, faces, M_SAND)
    
    # ===== HOUSE =====
    send_status("Creating house...")
    HX, HY = 1.0, 1.5
    
    for px, py in [(HX-0.8, HY-0.6), (HX+0.8, HY-0.6), (HX-0.8, HY+0.6), (HX+0.8, HY+0.6)]:
        cyl(f"Stilt", 0.08, 1.4, 8, px, py, 0.5, M_WOOD)
    
    box("Deck", 2.6, 2.4, 0.08, HX, HY, 1.9, M_DECK)
    
    for px, py in [(HX-1.1, HY-1.0), (HX-0.4, HY-1.0), (HX+0.4, HY-1.0), (HX+1.1, HY-1.0),
                   (HX-1.1, HY+1.0), (HX+1.1, HY+1.0), (HX-1.1, HY+0.3), (HX+1.1, HY+0.3),
                   (HX-1.1, HY-0.3), (HX+1.1, HY-0.3)]:
        cyl(f"Rail", 0.02, 0.4, 6, px, py, 1.98, M_WOOD)
    box("RailF", 2.2, 0.025, 0.025, HX, HY-1.0, 2.28, M_WOOD)
    box("RailB", 2.2, 0.025, 0.025, HX, HY+1.0, 2.28, M_WOOD)
    box("RailL", 0.025, 2.0, 0.025, HX-1.1, HY, 2.28, M_WOOD)
    box("RailR", 0.025, 2.0, 0.025, HX+1.1, HY, 2.28, M_WOOD)
    
    box("Floor1", 1.5, 1.5, 1.3, HX, HY, 1.98, M_WALL)
    box("Floor2", 1.2, 1.2, 0.9, HX, HY, 3.3, M_WALL)
    box("Win", 0.25, 0.03, 0.25, HX, HY-0.62, 3.65, M_WOOD)
    
    box("Roof1", 1.7, 1.7, 0.4, HX, HY, 4.22, M_ROOF)
    box("Roof2", 1.1, 1.1, 0.3, HX, HY, 4.58, M_ROOF)
    box("Roof3", 0.4, 0.4, 0.15, HX, HY, 4.85, M_ROOF)
    
    # ===== DOCK (extending from island edge into water) =====
    send_status("Creating dock...")
    DY = -1.5
    for i in range(16):
        box(f"Plank{i}", 0.32, 1.2, 0.06, -5.5 - i*0.35, DY, 0.1, M_DOCK)
    for px in [-6.0, -7.5, -9.0, -10.5]:
        cyl(f"DP", 0.05, 0.7, 6, px, DY-0.5, -0.25, M_DOCK)
        cyl(f"DP", 0.05, 0.7, 6, px, DY+0.5, -0.25, M_DOCK)
    
    # ===== TREES =====
    send_status("Creating trees...")
    trees = [(-3.5, 4.0, 0.65, 0.95), (-5.0, 0.5, 0.5, 0.8), (4.5, 3.0, 0.6, 1.0),
             (5.5, 0, 0.45, 0.85), (4.0, -2.5, 0.35, 0.75), (-3.0, -4.0, 0.3, 0.7)]
    for i, (tx, ty, tz, s) in enumerate(trees):
        cyl(f"T{i}", 0.07*s, 1.2*s, 6, tx, ty, tz, M_TRUNK)
        for j, (fh, fs) in enumerate([(1.0, 0.9), (1.4, 0.65), (1.75, 0.4)]):
            m = M_LEAF2 if j == 1 else M_LEAF
            box(f"L{i}{j}", fs*s, fs*s, fs*0.55*s, tx, ty, tz + fh*s, m)
    
    # ===== ROCKS =====
    send_status("Creating rocks...")
    box("R1", 0.5, 0.4, 0.35, -1.5, -3.5, 0.25, M_ROCK)
    box("R2", 0.35, 0.28, 0.22, -0.9, -3.3, 0.2, M_ROCK)
    box("R3", 0.2, 0.18, 0.14, -1.7, -3.2, 0.15, M_ROCK)
    
    # ===== LIGHTING =====
    send_status("Setting up lighting...")
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 4.0
    sun.color = (1.0, 0.97, 0.92)
    sun_obj = bpy.data.objects.new("Sun", sun)
    sun_obj.rotation_euler = (0.75, 0.15, 0.6)
    bpy.context.collection.objects.link(sun_obj)
    
    fill = bpy.data.lights.new("Fill", "SUN")
    fill.energy = 1.0
    fill_obj = bpy.data.objects.new("Fill", fill)
    fill_obj.rotation_euler = (0.5, 0, -0.7)
    bpy.context.collection.objects.link(fill_obj)
    
    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.28, 0.50, 0.58, 1.0)
        bg.inputs["Strength"].default_value = 1.0
    
    # ===== CAMERA =====
    send_status("Setting up camera...")
    cam = bpy.data.cameras.new("Camera")
    cam.lens = 35
    cam_obj = bpy.data.objects.new("Camera", cam)
    cam_obj.location = (20, -20, 14)
    cam_obj.rotation_euler = (1.0, 0, 0.78)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    # ===== RENDER =====
    send_status("Rendering...")
    bpy.context.scene.render.engine = 'BLENDER_EEVEE_NEXT'
    bpy.context.scene.render.resolution_x = 1280
    bpy.context.scene.render.resolution_y = 720
    bpy.context.scene.render.filepath = "D:/blender/blender_mcp_bridge/island_render.png"
    bpy.context.scene.eevee.use_soft_shadows = True
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath="D:/blender/blender_mcp_bridge/island_scene.blend")
    
    send_status("Done!")

main()
