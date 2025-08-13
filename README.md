# Component Reorientation - Fusion 360 Add-in

A Fusion 360 add-in that allows users to reorient selected components while maintaining the same orientation of the bodies inside them. This tool is particularly useful for assembly work where you need to change the orientation of a component without affecting its internal geometry.

## Features

- **Component Reorientation**: Select a planar face and reorient the entire component
- **Body Preservation**: Maintains the internal body orientations during reorientation
- **Interactive Triad Control**: Use the triad input for precise rotation control
- **Validation System**: Built-in error checking to prevent invalid operations
- **Assembly Safety**: Prevents reorientation of assembly components and root components

## Requirements

- **Operating System**: macOS (as specified in the manifest)
- **Software**: Autodesk Fusion 360
- **Python**: Python 3.x (included with Fusion 360)

## Installation for macOS

### Method 1: Manual Installation (Recommended)

1. **Download the Add-in**

   - Clone or download this repository to your local machine
   - Ensure all files are preserved in their directory structure

2. **Locate Fusion 360 Add-ins Directory**

   - Open Finder
   - Press `Cmd + Shift + G` to open "Go to Folder"
   - Navigate to: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`
   - If the `AddIns` folder doesn't exist, create it

3. **Install the Add-in**

   - Copy the entire `ComponentReorientation` folder to the `AddIns` directory
   - The final path should be: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/ComponentReorientation/`

4. **Restart Fusion 360**
   - Close Fusion 360 completely
   - Reopen Fusion 360
   - The add-in should automatically load

### Method 2: Using Terminal

```bash
# Navigate to your Downloads or project directory
cd ~/Downloads/ComponentReorientation

# Create the AddIns directory if it doesn't exist
mkdir -p ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/AddIns/

# Copy the add-in to the AddIns directory
cp -R . ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/AddIns/ComponentReorientation/
```

## Usage

1. **Launch the Command**

   - In Fusion 360, navigate to the **Solid** workspace
   - Look for the **Scripts and Add-ins** panel
   - Click the **"Reorient Component"** button

2. **Select a Face**

   - Choose a planar face on the component you want to reorient
   - The face should be on a component with only one body (not an assembly)

3. **Adjust Orientation**

   - Use the triad control to adjust the rotation as needed
   - The Z-rotation control will become available after face selection

4. **Execute**
   - Click **OK** to apply the reorientation
   - The component will be reoriented while preserving internal body geometry

## Project Structure

```
ComponentReorientation/
├── ComponentReorientation.manifest    # Add-in configuration
├── ComponentReorientation.py          # Main add-in entry point
├── config.py                         # Configuration variables
├── AddInIcon.svg                     # Add-in icon
├── commands/
│   └── reorientComponent/
│       ├── entry.py                  # Main command implementation
│       ├── resources/                # Command icons
│       └── __init__.py
└── lib/
    └── fusionAddInUtils/             # Utility functions
```

## Key Files

- **`entry.py`** - Contains the main command logic for component reorientation

  - Implements face selection, transformation calculations, and component manipulation
  - Handles user input validation and error reporting
  - Manages the command dialog and user interface

- **`ComponentReorientation.py`** - Main add-in entry point that registers the command
- **`config.py`** - Configuration settings including company name and add-in name
- **`ComponentReorientation.manifest`** - Add-in metadata and system requirements

## Troubleshooting

### Add-in Not Appearing

- Ensure the add-in is in the correct directory path
- Check that all files are present and not corrupted
- Restart Fusion 360 completely
- Verify the manifest file is valid JSON

### Command Errors

- Ensure you're selecting a planar face on a single-body component
- Avoid selecting faces on assembly components or the root component
- Check the error log in the command dialog for specific error messages

### Performance Issues

- Large components may take longer to process
- Ensure adequate system resources are available
- Close unnecessary Fusion 360 documents

## Development

This add-in is built using the Fusion 360 Python API. The main functionality is implemented in `commands/reorientComponent/entry.py`, which contains:

- Command creation and UI setup
- Face selection and validation
- Transformation matrix calculations
- Component manipulation logic
- Error handling and user feedback

## License

This project is provided as-is for educational and personal use.

## Support

For issues or questions:

1. Check the error messages in the command dialog
2. Verify the installation path and file structure
3. Ensure Fusion 360 is up to date
4. Check the Fusion 360 API documentation for compatibility

## Version History

- Current version supports macOS
- Designed for Fusion 360 compatibility
- Includes validation and error handling systems
