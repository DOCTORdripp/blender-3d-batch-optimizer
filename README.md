<div align="center">

<img src="blender-3d-batch-optimizer.png" alt="Blender 3D Batch Optimizer" width="400">

# 🎯 GLTF/GLB/VRM Bulk Optimizer for Blender

<p align="center">
  <strong>A comprehensive Python script for batch processing .gltf, .glb, and .vrm files in Blender</strong>
</p>

<p align="center">
  Automatically downscales textures, applies smart compression, and re-exports 3D files with minimal quality loss while preserving format-specific features.
</p>

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-requirements">Requirements</a> •
  <a href="#%EF%B8%8F-installation--setup">Installation</a> •
  <a href="#-usage">Usage</a> •
  <a href="#-blender-addon-gui-version">Blender Addon</a> •
  <a href="#-license">License</a>
</p>

</div>

## 🆕 Recent Updates

<div align="center">

### **🎯 Major Enhancement: True JPEG Quality Control**

**v2.1 - November 2024**
- ✅ **Fixed JPEG Quality**: Quality settings now actually affect output file sizes!
- ✅ **Force Compression**: Real compression via temporary file save/reload cycles
- ✅ **Enhanced Specular Removal**: Complete removal of specular tint textures and nodes
- ✅ **Improved Error Handling**: Better socket type validation and error recovery
- ✅ **Better Compression Ratios**: Achieving 75%+ file size reduction with quality control

</div>

## ✨ Features

<table>
<tr>
<td width="50%">

### 🔄 **Multi-Format Processing**
- ✅ **GLB files** - Binary single-file format
- ✅ **GLTF files** - Text-based multi-file format  
- ✅ **VRM files** - Avatar format with bones & expressions

### 🎨 **Smart Optimization**
- ✅ **Texture downscaling** to configurable resolution
- ✅ **Smart compression** with quality control (JPEG for color, PNG for normal maps)
- ✅ **Specular removal** for material optimization
- ✅ **Format preservation** options for compatibility

</td>
<td width="50%">

### 🚀 **Advanced Features**
- ✅ **Embedded texture support** for all formats
- ✅ **Real-time progress reporting** with compression ratios
- ✅ **Force compression** with actual JPEG quality control
- ✅ **Robust error handling** with batch continuation
- ✅ **Headless operation** for server environments

### ⚙️ **User-Friendly**
- ✅ **Skip existing files** option
- ✅ **VRM avatar preservation** (bones, physics, expressions)
- ✅ **Cross-platform support** (Windows/Linux/macOS)

</td>
</tr>
</table>

## 📋 Requirements

<div align="center">

| Component | Requirement | Notes |
|-----------|-------------|-------|
| **🔧 Blender** | Version 3.0+ | With Python API support |
| **💻 OS** | Windows/Linux/macOS | Tested on Windows |
| **📦 VRM Addon** | Optional | Only for .vrm files - [Download here](https://vrm-addon-for-blender.info/en/) |
| **📁 Input** | Directory with files | Supports .glb, .gltf, .vrm |
| **📂 Output** | Directory for results | Automatically created |

</div>

## 🛠️ Installation & Setup

<details>
<summary><strong>📥 Step 1: Download the Script</strong></summary>

Save `glb_bulk_optimizer.py` to your desired location on your computer.

</details>

<details>
<summary><strong>🔌 Step 2: Install VRM Addon (Optional)</strong></summary>

Only needed if processing .vrm files:

- **Blender 4.2+**: Install from Blender Extensions Platform
- **Blender 2.93-4.1**: Download from [VRM Add-on for Blender](https://vrm-addon-for-blender.info/en/)

</details>

<details>
<summary><strong>⚙️ Step 3: Configure Directories</strong></summary>

Edit the script to set your input/output paths:

```python
# Configure these paths in the script
INPUT_DIR = r"C:\path\to\input\glb\files"
OUTPUT_DIR = r"C:\path\to\output\glb\files"
```

</details>

<details>
<summary><strong>🎛️ Step 4: Optional Settings (Advanced)</strong></summary>

Customize these variables at the top of the script:

```python
TARGET_RESOLUTION = 512       # Target texture resolution
SKIP_EXISTING = True          # Skip files that already exist in output
TEXTURE_FORMAT = 'AUTO'       # 'AUTO', 'JPEG', or 'PNG'
JPEG_QUALITY = 80             # JPEG compression quality (1-100) - NOW WORKS!
REMOVE_SPECULAR = True        # Remove specular reflections for better optimization
AGGRESSIVE_JPEG_CONVERSION = True  # Convert more textures to JPEG
FORCE_COMPRESSION = True      # Force actual compression with quality settings
PRESERVE_FORMAT = True        # Keep original formats vs convert to GLB
VERBOSE = True                # Enable detailed logging
```

</details>

## 🚀 Usage

<div align="center">

### **🎯 Quick Start Command**

```cmd
"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe" --background --python glb_bulk_optimizer.py
```

</div>

### 🔍 **Finding Your Blender Installation**

<details>
<summary><strong>📍 Windows - Locate Blender Path</strong></summary>

1. **Right-click** your Blender desktop shortcut
2. **Select** "Properties" 
3. **Copy** the path from the "Target" field
4. **Replace** the example path above with your actual path

**Common Windows paths:**
- `"C:\Program Files\Blender Foundation\Blender 4.0\blender.exe"`
- `"C:\Program Files\Blender Foundation\Blender 3.6\blender.exe"`
- `"C:\Users\%USERNAME%\AppData\Local\Programs\Blender Foundation\Blender 4.0\blender.exe"`

</details>

<details>
<summary><strong>🐧 Linux / 🍎 macOS</strong></summary>

```bash
# macOS
/Applications/Blender.app/Contents/MacOS/Blender --background --python glb_bulk_optimizer.py

# Linux (typical path)
/usr/bin/blender --background --python glb_bulk_optimizer.py
```

</details>

<details>
<summary><strong>⚡ Advanced Users (PATH configured)</strong></summary>

```bash
blender --background --python glb_bulk_optimizer.py
```

</details>

## 🎨 Blender Addon (GUI Version)

<div align="center">

### **🖥️ User-Friendly Graphical Interface**

For users who prefer a visual interface within Blender, we provide a complete addon version with an intuitive GUI.

</div>

<details>
<summary><strong>📦 Addon Installation</strong></summary>

1. **Download** the `3d-batch-optimizer-blender_addon.zip` file from this repository
2. **Open Blender** (version 3.0 or higher)
3. **Go to** Edit → Preferences → Add-ons
4. **Click** "Install..." button
5. **Select** the downloaded zip file
6. **Enable** the "Bulk 3D Optimizer" addon by checking the checkbox
7. **Save Preferences** to make it permanent

</details>

<details>
<summary><strong>🎛️ Using the Addon</strong></summary>

1. **Open Blender** and switch to any 3D viewport
2. **Look for** the "Bulk Optimizer" tab in the sidebar (press `N` if sidebar is hidden)
3. **Configure** your settings:
   - **Input Directory**: Browse and select folder containing your 3D files
   - **Output Directory**: Choose where to save optimized files
   - **Target Resolution**: Set texture size (512 recommended)
   - **Texture Format**: Choose AUTO, JPEG, or PNG
   - **Additional Options**: Skip existing files, preserve formats, etc.
4. **Click** "Start Optimization" to begin processing
5. **Monitor Progress** through Blender's info panel and console

</details>

<details>
<summary><strong>✨ Addon Features</strong></summary>

### **🖱️ Point-and-Click Interface**
- **Directory Browser**: Easy folder selection with visual feedback
- **Real-time Validation**: Instant warnings for invalid settings
- **Progress Reporting**: Live updates in Blender's UI system

### **⚙️ Visual Settings Control**
- **Slider Controls**: Intuitive resolution and quality adjustment
- **Dropdown Menus**: Easy format selection
- **Toggle Switches**: Simple on/off options
- **Smart Defaults**: Pre-configured optimal settings

### **🔄 Seamless Integration**
- **Native Blender UI**: Follows Blender's design standards
- **Sidebar Panel**: Always accessible in 3D viewport
- **Error Handling**: Graceful failure handling that won't crash Blender
- **Memory Management**: Optimized for Blender's addon environment

</details>

<details>
<summary><strong>🆚 Command Line vs Addon Comparison</strong></summary>

<div align="center">

| Feature | Command Line Script | Blender Addon |
|---------|-------------------|---------------|
| **🎯 Ease of Use** | Technical users | All skill levels |
| **🖥️ Interface** | Text-based configuration | Visual GUI controls |
| **⚡ Automation** | Perfect for scripting | Point-and-click operation |
| **🔧 Integration** | Standalone execution | Built into Blender |
| **📊 Progress Feedback** | Console output | Blender UI updates |
| **🎛️ Settings** | Edit script file | Visual controls |
| **🚀 Best For** | Batch automation, servers | Interactive use, artists |

</div>

**💡 Recommendation**: 
- Use the **Command Line Script** for automated workflows, batch processing, or server environments
- Use the **Blender Addon** for interactive work, learning, or when you prefer visual interfaces

</details>

<details>
<summary><strong>🔧 Addon Troubleshooting</strong></summary>

**Addon doesn't appear in sidebar:**
- Press `N` to show/hide the sidebar in 3D viewport
- Make sure the addon is enabled in Preferences → Add-ons
- Try switching to a different workspace and back

**"⚠️ Select input directory" warning:**
- Click the folder icon next to Input field
- Navigate to a folder containing .glb, .gltf, or .vrm files
- Ensure the folder path doesn't contain special characters

**VRM files not processing:**
- Install the VRM addon from [VRM Add-on for Blender](https://vrm-addon-for-blender.info/en/)
- Enable it in Add-ons preferences
- Restart Blender after installation

**Processing seems stuck:**
- Check Blender's console (Window → Toggle System Console on Windows)
- Large files may take several minutes to process
- Memory usage can be high - close other applications

</details>

---

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_RESOLUTION` | `512` | Target texture resolution (e.g., 512, 1024, 256) |
| `SKIP_EXISTING` | `True` | Skip processing if output file already exists |
| `TEXTURE_FORMAT` | `'AUTO'` | Texture format: `'AUTO'`, `'JPEG'`, `'PNG'` |
| `JPEG_QUALITY` | `80` | JPEG compression quality (1-100) - **Fixed to work properly!** |
| `REMOVE_SPECULAR` | `True` | Remove specular reflections for better compression |
| `AGGRESSIVE_JPEG_CONVERSION` | `True` | Convert more textures to JPEG format |
| `FORCE_COMPRESSION` | `True` | Force actual compression using file save/reload |
| `PRESERVE_FORMAT` | `True` | Keep original formats vs convert to GLB |
| `VERBOSE` | `True` | Enable detailed progress logging |

### Format Options

#### **Texture Formats:**
- **`'AUTO'`** (Recommended): Smart format selection:
  - JPEG for color/diffuse textures
  - PNG for normal maps, roughness, metallic, alpha textures
- **`'JPEG'`**: Force all textures to JPEG (smaller files, some quality loss)
- **`'PNG'`**: Force all textures to PNG (larger files, lossless)

#### **File Format Preservation:**
- **`PRESERVE_FORMAT = True`**: Keep original file formats:
  - `.gltf` files stay as `.gltf` (better compatibility)
  - `.glb` files stay as `.glb`
  - `.vrm` files stay as `.vrm`
- **`PRESERVE_FORMAT = False`**: Convert for efficiency:
  - `.gltf` files convert to `.glb` (smaller, single file)
  - `.vrm` files always stay as `.vrm` (preserve avatar features)

## Example Output

```
[INFO] Starting GLTF/GLB/VRM Bulk Optimizer
[INFO] Input directory: C:\Models\Input
[INFO] Output directory: C:\Models\Optimized
[INFO] Target resolution: 512x512
[INFO] Found 18 .glb/.gltf/.vrm files to process

--- Processing file 1/18 ---
[INFO] Processing: character_01.glb
[INFO] Imported GLTF/GLB file: character_01.glb
[INFO] Material 'Character_Material' - Specular current value: 0.5
[INFO] Set Specular to 0.0 on material: Character_Material
[INFO] Converting PNG 'BaseColor' to JPEG (no alpha channel detected)
[INFO] Successfully compressed 'BaseColor' to JPEG with quality 80%
[INFO] Resizing 'BaseColor' from 2048x2048 to 512x512
[INFO] Keeping 'Normal' as PNG due to normal map usage
[INFO] Resizing 'Normal.png' from 2048x2048 to 512x512
[INFO] Processed 3 textures across 2 materials
[INFO] Successfully exported: character_01.glb
[INFO] Size: 45.2MB → 8.9MB (-80.3%)

--- Processing file 5/18 ---
[INFO] Processing: avatar.vrm
[INFO] Imported VRM file: avatar.vrm
[INFO] Resizing 'Face.png' from 1024x1024 to 512x512
[INFO] Processed 5 textures across 3 materials
[INFO] Successfully exported: avatar.vrm
[INFO] Size: 28.1MB → 8.3MB (-70.5%)

...

==================================================
PROCESSING COMPLETE
==================================================
Total files found: 18
Successfully processed: 17
Skipped (already exist): 0
Errors: 1
Total size reduction: 520.3MB → 128.4MB (-75.3%)
```

## How It Works

1. **File Detection**: Automatically finds .glb, .gltf, and .vrm files in input directory
2. **Scene Clearing**: Clears Blender scene for each file to prevent conflicts
3. **Smart Import**: Uses appropriate importer based on file type (GLTF/VRM)
4. **Material Optimization**:
   - Removes specular reflections and specular tint textures
   - Cleans material properties for better compression
   - Preserves essential material features
5. **Texture Processing**: 
   - Scans all materials for image texture nodes
   - Performs in-memory texture resizing to target resolution
   - **NEW**: Applies actual JPEG compression with quality control
   - Smart format detection (alpha channel preservation)
   - Maintains embedded texture status for GLB/VRM files
   - Preserves material connections and references
6. **Format-Aware Export**: 
   - VRM files maintain VRM format with all avatar features
   - GLTF files can stay as GLTF or convert to GLB based on settings
   - GLB files stay as optimized GLB format
7. **Progress Tracking**: Real-time reporting of file sizes and compression ratios

## Tips & Best Practices

### Choosing Target Resolution
- **512x512**: Good balance for most web/mobile applications
- **256x256**: Maximum compression for low-end devices
- **1024x1024**: Higher quality for desktop applications
- **2048x2048**: Minimal compression, mainly for format conversion

### File Type Selection
- **GLTF files**: Best compatibility with 3D viewers and web applications
- **GLB files**: Single-file format, ideal for apps and games
- **VRM files**: Avatar format for VTubers, VRChat, and metaverse applications

### Texture Format Selection
- Use **AUTO** for best results (recommended)
- Use **JPEG** for maximum compression when quality loss is acceptable
- Use **PNG** when you need lossless compression or have transparency

### JPEG Quality Control
- **Quality 40-60**: Maximum compression for web/mobile use (smaller files)
- **Quality 70-85**: Good balance of size and quality (recommended)
- **Quality 90-100**: Higher quality for professional work (larger files)
- **Note**: Quality settings now actually work and affect file sizes!

### Format Preservation
- **PRESERVE_FORMAT = True**: Better compatibility with 3D viewers
- **PRESERVE_FORMAT = False**: Smaller file sizes, fewer files to manage

### Performance Tips
- Close other applications when processing large batches
- Use SSD storage for faster I/O
- Monitor system resources during processing

## Troubleshooting

### Common Issues

**"Error: This script must be run within Blender"**
- Make sure you're running the script with Blender's Python: `blender --background --python script.py`

**"No .glb, .gltf, or .vrm files found in input directory"**
- Check that `INPUT_DIR` path is correct
- Ensure files have `.glb`, `.gltf`, or `.vrm` extensions

**"Error importing GLTF/GLB/VRM file"**
- File may be corrupted or invalid
- For VRM files: Ensure VRM addon is installed from [VRM Add-on for Blender](https://vrm-addon-for-blender.info/en/) and enabled
- Check Blender version compatibility (supports 2.93 to 4.4)
- Try opening the file manually in Blender first

**Out of memory errors**
- Reduce `TARGET_RESOLUTION` for very large texture files
- Process fewer files at once
- Increase system RAM or virtual memory

### Error Handling
The script includes comprehensive error handling:
- Individual file failures won't stop batch processing
- Detailed error messages help identify problematic files
- Processing continues with remaining files

## Advanced Usage

### Custom Resolution Per File Type
You can modify the script to use different resolutions based on file names:

```python
def get_target_resolution(filename):
    if "highres" in filename.lower():
        return 1024
    elif "mobile" in filename.lower():
        return 256
    else:
        return 512
```

### Batch Processing with Multiple Directories
Process multiple input directories by modifying the main function to loop through directory lists.

## 📄 License

<div align="center">

**Licensed under the Apache License, Version 2.0**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

<details>
<summary><strong>📋 License Details</strong></summary>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

</details>

</div>

## 📊 File Format Support Summary

<div align="center">

| Format | Input | Output | Features Preserved | Use Case |
|--------|--------|--------|-------------------|----------|
| **🔷 GLB** | `.glb` | `.glb` | All GLB features | Single-file 3D models |
| **📄 GLTF** | `.gltf` | `.gltf` or `.glb`* | Material structure | Multi-file 3D models |
| **🎭 VRM** | `.vrm` | `.vrm` | Avatar bones, expressions, physics | VTuber avatars, metaverse |

<sub>*Output format depends on `PRESERVE_FORMAT` setting</sub>

</div>

---

<div align="center">

## 🤝 Support & Contributing

<p>
  <strong>Need help or want to contribute?</strong><br>
  Check the items below for common solutions
</p>

**📋 Troubleshooting Checklist:**
- ✅ Blender version compatibility (3.0+)
- ✅ VRM addon installation (for .vrm files) 
- ✅ File format validity and corruption
- ✅ System resource availability
- ✅ Directory permissions and paths

<p>
  <a href="https://github.com/DOCTORdripp/blender-3d-batch-optimizer/issues">🐛 Report Issues</a> •
  <a href="#license">📄 License</a>
</p>

</div> 