#!/usr/bin/env python3
"""
GLTF/GLB/VRM Bulk Optimizer for Blender
Batch processes .gltf, .glb, and .vrm files to downscale textures and reduce file sizes.

Usage:
    blender --background --python glb_bulk_optimizer.py

Requirements:
    - Blender 3.0+ with Python API
    - VRM addon installed (for VRM file support)
    - Input and output directories configured below
"""

import bpy
import bmesh
import os
import sys
import traceback
from pathlib import Path
from mathutils import Vector
import tempfile
import shutil

# ================================
# CONFIGURATION VARIABLES
# ================================

# Input directory containing .glb files to process
INPUT_DIR = r"C:\Users\docto\Documents\GitHub\GLB-bulk-optimize\models"

# Output directory for processed .glb files
OUTPUT_DIR = r"C:\Users\docto\Documents\GitHub\GLB-bulk-optimize\models-optimized"

# Target texture resolution (width x height)
TARGET_RESOLUTION = 512

# Skip files that already exist in output directory
SKIP_EXISTING = True

# Texture compression format ('JPEG', 'PNG', or 'AUTO')
# AUTO will use JPEG for most textures, PNG for normal maps and masks
TEXTURE_FORMAT = 'AUTO'

# JPEG quality (1-100, only applies if using JPEG compression)
JPEG_QUALITY = 85

# Preserve original file format (True = GLTF stays GLTF, False = convert GLTF to GLB)
PRESERVE_FORMAT = False

# Enable verbose logging
VERBOSE = True

# ================================
# UTILITY FUNCTIONS
# ================================

def log(message, level="INFO"):
    """Print formatted log message."""
    print(f"[{level}] {message}")

def clear_scene():
    """Clear all objects, materials, and images from the current scene."""
    try:
        # Clear all mesh objects
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        # Clear orphaned data
        for block in bpy.data.meshes:
            bpy.data.meshes.remove(block)
        for block in bpy.data.materials:
            bpy.data.materials.remove(block)
        for block in bpy.data.images:
            bpy.data.images.remove(block)
        for block in bpy.data.textures:
            bpy.data.textures.remove(block)
        for block in bpy.data.node_groups:
            bpy.data.node_groups.remove(block)
            
        # Clear collections
        for collection in bpy.data.collections:
            bpy.data.collections.remove(collection)
            
        if VERBOSE:
            log("Scene cleared successfully")
            
    except Exception as e:
        log(f"Warning: Error clearing scene: {e}", "WARNING")

def get_texture_format(image_name, node_type=None):
    """Determine optimal texture format based on image type."""
    if TEXTURE_FORMAT == 'PNG':
        return 'PNG'
    elif TEXTURE_FORMAT == 'JPEG':
        return 'JPEG'
    else:  # AUTO
        name_lower = image_name.lower()
        # Use PNG for normal maps, roughness, metallic, and alpha textures
        if any(keyword in name_lower for keyword in ['normal', 'nrm', 'bump', 'roughness', 'metallic', 'alpha', 'opacity', 'mask']):
            return 'PNG'
        # Use JPEG for color/diffuse textures
        return 'JPEG'

def resize_image(image, target_width, target_height):
    """Resize a Blender image to target dimensions."""
    try:
        if image.size[0] <= target_width and image.size[1] <= target_height:
            if VERBOSE:
                log(f"Image '{image.name}' already at or below target resolution ({image.size[0]}x{image.size[1]})")
            return False
            
        if VERBOSE:
            log(f"Resizing '{image.name}' from {image.size[0]}x{image.size[1]} to {target_width}x{target_height}")
        
        # Scale the image
        image.scale(target_width, target_height)
        image.update()
        return True
        
    except Exception as e:
        log(f"Error resizing image '{image.name}': {e}", "ERROR")
        return False

def process_material_textures(material):
    """Process all textures in a material."""
    if not material.use_nodes:
        return 0
    
    processed_count = 0
    
    for node in material.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            image = node.image
            
            # Skip if image is already processed
            if hasattr(image, '_bulk_processed'):
                continue
                
            original_packed = image.packed_file is not None
            
            # Store original image data in memory for processing
            if image.size[0] > TARGET_RESOLUTION or image.size[1] > TARGET_RESOLUTION:
                if VERBOSE:
                    log(f"Resizing '{image.name}' from {image.size[0]}x{image.size[1]} to {TARGET_RESOLUTION}x{TARGET_RESOLUTION}")
                
                # Resize the image in memory
                image.scale(TARGET_RESOLUTION, TARGET_RESOLUTION)
                image.update()
                processed_count += 1
                
                if VERBOSE:
                    log(f"Successfully resized texture '{image.name}'")
            else:
                if VERBOSE:
                    log(f"Image '{image.name}' already at or below target resolution ({image.size[0]}x{image.size[1]})")
            
            # If it was originally packed, keep it packed (embedded in GLB)
            if original_packed and not image.packed_file:
                try:
                    image.pack()
                    if VERBOSE:
                        log(f"Re-packed texture '{image.name}' for embedding")
                except Exception as e:
                    log(f"Warning: Could not re-pack texture '{image.name}': {e}", "WARNING")
            
            # Mark as processed
            image['_bulk_processed'] = True
    
    return processed_count

def get_file_type(filepath):
    """Determine file type based on extension."""
    ext = filepath.suffix.lower()
    if ext in ['.glb', '.gltf']:
        return 'gltf'
    elif ext == '.vrm':
        return 'vrm'
    else:
        return 'unknown'

def import_file(input_path):
    """Import file based on its type."""
    file_type = get_file_type(input_path)
    
    if file_type == 'gltf':
        try:
            bpy.ops.import_scene.gltf(filepath=str(input_path))
            if VERBOSE:
                log(f"Imported GLTF/GLB file: {input_path.name}")
            return True
        except Exception as e:
            log(f"Error importing GLTF/GLB file '{input_path}': {e}", "ERROR")
            # Try fallback for animation issues
            if "bone" in str(e).lower() or "animation" in str(e).lower():
                log(f"Animation/bone error - attempting to continue without animations", "WARNING")
                try:
                    bpy.ops.import_scene.gltf(filepath=str(input_path), import_pack_images=True)
                    if VERBOSE:
                        log(f"Imported GLTF/GLB file without animations: {input_path.name}")
                    return True
                except Exception as e2:
                    log(f"Failed to import even without animations: {e2}", "ERROR")
                    return False
            else:
                return False
    
    elif file_type == 'vrm':
        try:
            bpy.ops.import_scene.vrm(filepath=str(input_path))
            if VERBOSE:
                log(f"Imported VRM file: {input_path.name}")
            return True
        except Exception as e:
            log(f"Error importing VRM file '{input_path}': {e}", "ERROR")
            return False
    
    else:
        log(f"Unsupported file type: {input_path.suffix}", "ERROR")
        return False

def export_file(output_path, file_type):
    """Export file based on desired output type."""
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if file_type == 'vrm':
            # Export as VRM
            try:
                bpy.ops.export_scene.vrm(filepath=str(output_path))
            except TypeError as e:
                # Fallback for different VRM addon versions
                if VERBOSE:
                    log(f"Using fallback VRM export parameters due to: {e}")
                bpy.ops.export_scene.vrm(filepath=str(output_path))
        
        elif file_type == 'gltf':
            # Export as GLTF (separate files) for better compatibility
            try:
                bpy.ops.export_scene.gltf(
                    filepath=str(output_path),
                    export_format='GLTF_SEPARATE',
                    export_materials='EXPORT',
                    export_colors=True,
                    export_cameras=False,
                    export_lights=False,
                    export_animations=True,
                    export_yup=True,
                    export_apply=False,
                    export_texcoords=True,
                    export_normals=True,
                    export_draco_mesh_compression_enable=False,
                    export_tangents=False,
                    use_selection=False,
                    use_visible=False,
                    use_renderable=False,
                    use_active_collection=False,
                    use_active_scene=False
                )
            except TypeError as e:
                # Fallback for older Blender versions
                if VERBOSE:
                    log(f"Using fallback GLTF export parameters due to: {e}")
                bpy.ops.export_scene.gltf(
                    filepath=str(output_path),
                    export_format='GLTF_SEPARATE'
                )
        
        else:
            # Export as GLB (binary format)
            try:
                bpy.ops.export_scene.gltf(
                    filepath=str(output_path),
                    export_format='GLB',
                    export_materials='EXPORT',
                    export_colors=True,
                    export_cameras=False,
                    export_lights=False,
                    export_animations=True,
                    export_yup=True,
                    export_apply=False,
                    export_texcoords=True,
                    export_normals=True,
                    export_draco_mesh_compression_enable=False,
                    export_tangents=False,
                    use_selection=False,
                    use_visible=False,
                    use_renderable=False,
                    use_active_collection=False,
                    use_active_scene=False
                )
            except TypeError as e:
                # Fallback for older Blender versions with minimal parameters
                if VERBOSE:
                    log(f"Using fallback GLB export parameters due to: {e}")
                bpy.ops.export_scene.gltf(
                    filepath=str(output_path),
                    export_format='GLB'
                )
        
        return True
        
    except Exception as e:
        log(f"Error exporting file '{output_path}': {e}", "ERROR")
        return False

def process_glb_file(input_path, output_path):
    """Process a single 3D file (GLB/GLTF/VRM)."""
    try:
        log(f"Processing: {input_path.name}")
        
        # Clear the scene
        clear_scene()
        
        # Import the file based on its type
        if not import_file(input_path):
            return False
        
        # Process materials and textures
        total_textures_processed = 0
        processed_materials = 0
        
        for material in bpy.data.materials:
            if material.users > 0:  # Only process materials that are actually used
                texture_count = process_material_textures(material)
                if texture_count > 0:
                    processed_materials += 1
                    total_textures_processed += texture_count
        
        log(f"Processed {total_textures_processed} textures across {processed_materials} materials")
        
        # Export the processed file (output_path already has correct extension)
        input_file_type = get_file_type(input_path)
        
        if input_file_type == 'vrm':
            success = export_file(output_path, 'vrm')
        elif PRESERVE_FORMAT and input_file_type == 'gltf' and output_path.suffix.lower() == '.gltf':
            # Export as GLTF to maintain compatibility
            success = export_file(output_path, 'gltf')
        else:
            # Export as GLB
            success = export_file(output_path, 'glb')
        
        if success:
            log(f"Successfully exported: {output_path.name}")
            return True
        else:
            return False
            
    except Exception as e:
        log(f"Error processing GLTF/GLB file '{input_path}': {e}", "ERROR")
        traceback.print_exc()
        return False

def get_file_size_mb(filepath):
    """Get file size in megabytes."""
    try:
        return os.path.getsize(filepath) / (1024 * 1024)
    except:
        return 0

def main():
    """Main processing function."""
    log("Starting GLTF/GLB/VRM Bulk Optimizer")
    log(f"Input directory: {INPUT_DIR}")
    log(f"Output directory: {OUTPUT_DIR}")
    log(f"Target resolution: {TARGET_RESOLUTION}x{TARGET_RESOLUTION}")
    log(f"Texture format: {TEXTURE_FORMAT}")
    
    # Validate directories
    input_path = Path(INPUT_DIR)
    output_path = Path(OUTPUT_DIR)
    
    if not input_path.exists():
        log(f"Error: Input directory does not exist: {INPUT_DIR}", "ERROR")
        return
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all .glb, .gltf, and .vrm files
    glb_files = (list(input_path.glob("*.glb")) + list(input_path.glob("*.GLB")) + 
                 list(input_path.glob("*.gltf")) + list(input_path.glob("*.GLTF")) +
                 list(input_path.glob("*.vrm")) + list(input_path.glob("*.VRM")))
    
    if not glb_files:
        log("No .glb, .gltf, or .vrm files found in input directory", "WARNING")
        return
    
    log(f"Found {len(glb_files)} .glb/.gltf/.vrm files to process")
    
    # Process each file
    processed_count = 0
    skipped_count = 0
    error_count = 0
    total_size_before = 0
    total_size_after = 0
    
    for i, glb_file in enumerate(glb_files, 1):
        log(f"\n--- Processing file {i}/{len(glb_files)} ---")
        
        # Determine output filename based on input type and settings
        input_type = get_file_type(glb_file)
        if input_type == 'vrm':
            # VRM files always keep .vrm extension
            output_filename = glb_file.stem + '.vrm'
        elif PRESERVE_FORMAT:
            # Keep original format if preserve format is enabled
            output_filename = glb_file.name
        else:
            # Convert GLTF to GLB for efficiency
            output_filename = glb_file.stem + '.glb'
        
        output_file = output_path / output_filename
        
        # Skip if output file already exists and SKIP_EXISTING is True
        if SKIP_EXISTING and output_file.exists():
            log(f"Skipping existing file: {output_file.name}")
            skipped_count += 1
            continue
        
        # Record original file size
        original_size = get_file_size_mb(glb_file)
        total_size_before += original_size
        
        # Process the file
        success = process_glb_file(glb_file, output_file)
        
        if success:
            processed_count += 1
            new_size = get_file_size_mb(output_file)
            total_size_after += new_size
            compression_ratio = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
            log(f"Size: {original_size:.2f}MB → {new_size:.2f}MB ({compression_ratio:+.1f}%)")
        else:
            error_count += 1
    
    # Final summary
    log(f"\n{'='*50}")
    log("PROCESSING COMPLETE")
    log(f"{'='*50}")
    log(f"Total files found: {len(glb_files)}")
    log(f"Successfully processed: {processed_count}")
    log(f"Skipped (already exist): {skipped_count}")
    log(f"Errors: {error_count}")
    
    if processed_count > 0:
        overall_compression = ((total_size_before - total_size_after) / total_size_before * 100) if total_size_before > 0 else 0
        log(f"Total size reduction: {total_size_before:.2f}MB → {total_size_after:.2f}MB ({overall_compression:+.1f}%)")

if __name__ == "__main__":
    # Ensure we're running in Blender
    try:
        import bpy
    except ImportError:
        print("Error: This script must be run within Blender")
        print("Usage: blender --background --python glb_bulk_optimizer.py")
        sys.exit(1)
    
    # Set Blender to use CPU for rendering (more stable for batch processing)
    bpy.context.scene.cycles.device = 'CPU'
    
    # Run the main function
    main() 