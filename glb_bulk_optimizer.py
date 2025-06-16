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
JPEG_QUALITY = 80

# Preserve original file format (True = GLTF stays GLTF, False = convert GLTF to GLB)
PRESERVE_FORMAT = False

# Enable verbose logging
VERBOSE = True

# Remove specular tint textures and set specular to 0 (reduces file size)
REMOVE_SPECULAR = True

# Aggressive JPEG conversion for PNG textures (except those needing alpha)
AGGRESSIVE_JPEG_CONVERSION = True

# Force compression even when not resizing (helps reduce file size)
FORCE_COMPRESSION = True

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

def has_alpha_channel(image):
    """Check if image actually uses alpha channel (has transparency)."""
    try:
        if not image or not image.pixels:
            return False
        
        # Check if image has alpha channel data
        if len(image.pixels) % 4 != 0:
            return False  # No alpha channel in pixel data
        
        # Sample alpha values to see if any are not 1.0 (fully opaque)
        # Only check a sample of pixels for performance (every 100th pixel)
        pixels = image.pixels[:]
        alpha_values = pixels[3::4]  # Every 4th value is alpha
        
        # Sample every 100th alpha value for performance
        sample_step = max(1, len(alpha_values) // 1000)  # Check at most 1000 pixels
        
        # If any sampled alpha value is not 1.0, we need transparency
        for i in range(0, len(alpha_values), sample_step):
            if alpha_values[i] < 0.98:  # Small tolerance for floating point
                if VERBOSE:
                    log(f"Alpha channel detected in '{image.name}' (alpha value: {alpha_values[i]:.3f})")
                return True
        
        return False
    except Exception as e:
        if VERBOSE:
            log(f"Warning: Could not analyze alpha channel for '{image.name if image else 'unknown'}': {e}")
        # If we can't determine, be conservative and assume no alpha
        return False

def get_texture_format(image_name, node_type=None, image=None):
    """Determine optimal texture format based on image type and actual usage."""
    if TEXTURE_FORMAT == 'PNG':
        return 'PNG'
    elif TEXTURE_FORMAT == 'JPEG':
        return 'JPEG'
    else:  # AUTO - smart format selection
        name_lower = image_name.lower()
        
        # Always use PNG for normal maps, roughness, metallic (they need precision)
        if any(keyword in name_lower for keyword in ['normal', 'nrm', 'bump', 'roughness', 'metallic']):
            return 'PNG'
        
        # If aggressive JPEG conversion is enabled, check for actual alpha usage
        if AGGRESSIVE_JPEG_CONVERSION:
            # Only keep PNG if image actually uses alpha channel
            if image and has_alpha_channel(image):
                if VERBOSE:
                    log(f"Keeping '{image_name}' as PNG due to alpha channel usage")
                return 'PNG'
            else:
                # Convert PNG to JPEG for better compression
                if image and image.file_format == 'PNG':
                    if VERBOSE:
                        log(f"Converting PNG '{image_name}' to JPEG (no alpha channel detected)")
                return 'JPEG'
        else:
            # Conservative approach - check name patterns
            if any(keyword in name_lower for keyword in ['alpha', 'opacity', 'mask']):
                return 'PNG'
        
        # For everything else (diffuse, color, etc.), use JPEG for better compression
        return 'JPEG'

def clean_material_properties(material):
    """Remove specular tint and reduce specular to 0 for better compression."""
    if not REMOVE_SPECULAR:
        return
        
    try:
        if not material.use_nodes:
            # For materials without nodes, set basic specular properties
            if hasattr(material, 'specular_intensity'):
                material.specular_intensity = 0.0
            if hasattr(material, 'specular_color'):
                material.specular_color = (0.0, 0.0, 0.0)
            if VERBOSE:
                log(f"Set specular properties to 0 on non-node material: {material.name}")
            return
        
        nodes_to_remove = []
        links_to_remove = []
        
        # Log current specular values for debugging
        if VERBOSE:
            for node in material.node_tree.nodes:
                if node.type == 'BSDF_PRINCIPLED':
                    for input_name in ['Specular', 'Specular IOR Level', 'Specular Tint']:
                        if input_name in node.inputs:
                            input_socket = node.inputs[input_name]
                            log(f"Material '{material.name}' - {input_name} current value: {input_socket.default_value}")
        
        for node in material.node_tree.nodes:
            # Remove specular tint texture nodes
            if node.type == 'TEX_IMAGE' and node.image:
                image_name_lower = node.image.name.lower()
                node_name_lower = node.name.lower()
                
                # Check both image name and node name for specular tint
                if any(keyword in image_name_lower for keyword in ['specular_tint', 'spectint', 'spec_tint', 'specular tint']) or \
                   any(keyword in node_name_lower for keyword in ['specular_tint', 'spectint', 'spec_tint', 'specular tint']):
                    if VERBOSE:
                        log(f"Removing specular tint texture: {node.image.name} (node: {node.name})")
                    # Disconnect all links from this node
                    for output in node.outputs:
                        for link in output.links:
                            links_to_remove.append(link)
                    nodes_to_remove.append(node)
            
            # Set specular values to 0 on principled BSDF
            elif node.type == 'BSDF_PRINCIPLED':
                # Handle different input names for specular
                specular_inputs = []
                
                # Check for various specular input names
                for input_name in ['Specular', 'Specular IOR Level', 'Specular Tint']:
                    if input_name in node.inputs:
                        specular_inputs.append(node.inputs[input_name])
                
                for specular_input in specular_inputs:
                    try:
                        # Disconnect any links to specular input
                        for link in specular_input.links:
                            links_to_remove.append(link)
                        
                        # Set specular to 0
                        if specular_input.name == 'Specular Tint':
                            # Specular Tint can be float or color - check the socket type
                            if hasattr(specular_input, 'default_value'):
                                current_val = specular_input.default_value
                                if isinstance(current_val, (int, float)):
                                    specular_input.default_value = 1.0  # White for float
                                else:
                                    specular_input.default_value = (1.0, 1.0, 1.0, 1.0)  # White for color
                        else:
                            # Regular specular inputs should be 0
                            if hasattr(specular_input, 'default_value'):
                                if isinstance(specular_input.default_value, (int, float)):
                                    specular_input.default_value = 0.0
                                else:
                                    specular_input.default_value = (0.0, 0.0, 0.0, 1.0)
                        
                        if VERBOSE:
                            log(f"Set {specular_input.name} to {specular_input.default_value} on material: {material.name}")
                    
                    except Exception as e:
                        if VERBOSE:
                            log(f"Warning: Could not set {specular_input.name} on material {material.name}: {e}", "WARNING")
            
            # Also handle other specular-related nodes
            elif node.type in ['BSDF_GLOSSY', 'BSDF_ANISOTROPIC']:
                # Remove or minimize glossy/anisotropic nodes that add specular reflection
                if VERBOSE:
                    log(f"Found specular node type {node.type} in material {material.name} - marking for removal")
                nodes_to_remove.append(node)
        
        # Remove the marked links first
        for link in links_to_remove:
            try:
                material.node_tree.links.remove(link)
            except:
                pass  # Link might already be removed
        
        # Remove the marked nodes
        for node in nodes_to_remove:
            try:
                node_name = node.name
                material.node_tree.nodes.remove(node)
                if VERBOSE:
                    log(f"Successfully removed node '{node_name}' from material '{material.name}'")
            except Exception as e:
                if VERBOSE:
                    log(f"Warning: Could not remove node '{node.name}' from material '{material.name}': {e}", "WARNING")
            
    except Exception as e:
        log(f"Warning: Error cleaning material properties for '{material.name}': {e}", "WARNING")

def apply_texture_compression(image, target_format):
    """Apply texture compression by setting format and compressing via file save/reload."""
    try:
        if not image:
            return
        
        original_format = image.file_format
        was_packed = image.packed_file is not None
        
        if target_format == 'JPEG':
            if VERBOSE:
                log(f"Converting '{image.name}' to JPEG format (quality: {JPEG_QUALITY}%)")
            
            # Set JPEG format
            image.file_format = 'JPEG'
            
            # Set quality for export
            try:
                image.file_format_quality = JPEG_QUALITY / 100.0
            except AttributeError:
                # Fallback for older Blender versions
                bpy.context.scene.render.image_settings.quality = JPEG_QUALITY
            
            # Force compression by saving and reloading if needed
            if FORCE_COMPRESSION or original_format != 'JPEG':
                try:
                    import tempfile
                    import os
                    
                    # Save to temporary file with compression
                    temp_dir = tempfile.gettempdir()
                    temp_file = os.path.join(temp_dir, f"temp_{image.name}.jpg")
                    
                    # Set render settings for JPEG quality (used by image.save_render)
                    original_quality = bpy.context.scene.render.image_settings.quality
                    original_format = bpy.context.scene.render.image_settings.file_format
                    
                    bpy.context.scene.render.image_settings.file_format = 'JPEG'
                    bpy.context.scene.render.image_settings.quality = JPEG_QUALITY
                    
                    # Save with JPEG compression using render settings
                    image.filepath_raw = temp_file
                    image.save_render(temp_file)
                    
                    # Restore original render settings
                    bpy.context.scene.render.image_settings.quality = original_quality
                    bpy.context.scene.render.image_settings.file_format = original_format
                    
                    # Reload the compressed version
                    image.filepath = temp_file
                    image.source = 'FILE'
                    image.reload()
                    
                    # Pack if it was originally packed
                    if was_packed:
                        image.pack()
                    
                    # Clean up temp file
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                    
                    if VERBOSE:
                        log(f"Successfully compressed '{image.name}' to JPEG with quality {JPEG_QUALITY}%")
                        
                except Exception as e:
                    if VERBOSE:
                        log(f"Warning: Could not save/reload compress '{image.name}': {e}")
                    # Just set format without compression
                        
        elif target_format == 'PNG':
            image.file_format = 'PNG'
            if VERBOSE:
                log(f"Keeping '{image.name}' as PNG format")
        
        # Update the image
        image.update()
        
    except Exception as e:
        log(f"Warning: Error applying compression to '{image.name}': {e}", "WARNING")

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
            
            # Skip specular tint images that should have been removed
            image_name_lower = image.name.lower()
            node_name_lower = node.name.lower()
            if any(keyword in image_name_lower for keyword in ['specular_tint', 'spectint', 'spec_tint', 'specular tint']) or \
               any(keyword in node_name_lower for keyword in ['specular_tint', 'spectint', 'spec_tint', 'specular tint']):
                if VERBOSE:
                    log(f"Skipping specular tint texture that should have been removed: {image.name}")
                continue
                
            original_packed = image.packed_file is not None
            
            # Determine optimal format based on actual image content
            target_format = get_texture_format(image.name, node.type, image)
            
            # Apply texture compression format
            apply_texture_compression(image, target_format)
            
            # Count this as processed since we applied compression
            processed_count += 1
            
            # Resize if needed
            if image.size[0] > TARGET_RESOLUTION or image.size[1] > TARGET_RESOLUTION:
                if VERBOSE:
                    log(f"Resizing '{image.name}' from {image.size[0]}x{image.size[1]} to {TARGET_RESOLUTION}x{TARGET_RESOLUTION}")
                
                # Resize the image in memory
                image.scale(TARGET_RESOLUTION, TARGET_RESOLUTION)
                image.update()
                
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
        
        # First clean up all materials (remove specular tint, set specular to 0)
        if REMOVE_SPECULAR:
            for material in bpy.data.materials:
                if material.users > 0:  # Only process materials that are actually used
                    clean_material_properties(material)
        
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
    if REMOVE_SPECULAR:
        log("Specular removal: ENABLED")
    if AGGRESSIVE_JPEG_CONVERSION:
        log("Aggressive JPEG conversion: ENABLED")
    if FORCE_COMPRESSION:
        log("Force compression: ENABLED")
    if TEXTURE_FORMAT in ['AUTO', 'JPEG']:
        log(f"JPEG quality: {JPEG_QUALITY}%")
    
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