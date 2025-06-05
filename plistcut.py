import plistlib
import os
import sys
from PIL import Image
import re
import glob

def parse_rect(rect_str):
    # Parse string like "{{1560,430},{219,219}}" into coordinates and size
    match = re.match(r'{{(\d+),(\d+)},{(\d+),(\d+)}}', rect_str)
    if match:
        x, y, width, height = map(int, match.groups())
        return (x, y, width, height)
    return None

def find_matching_files(directory):
    # Find all plist files in the directory
    plist_files = glob.glob(os.path.join(directory, "*.plist"))
    if not plist_files:
        print(f"No plist files found in {directory}")
        return []
    
    # For each plist file, try to find a matching png file
    matching_pairs = []
    for plist_file in plist_files:
        base_name = os.path.splitext(plist_file)[0]
        png_file = base_name + ".png"
        if os.path.exists(png_file):
            matching_pairs.append((plist_file, png_file))
    
    if not matching_pairs:
        print(f"No matching png files found for plist files in {directory}")
    
    return matching_pairs

def process_sprite_sheet(plist_file, png_file, output_dir):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get the base name for the output subdirectory
    base_name = os.path.splitext(os.path.basename(plist_file))[0]
    sprite_output_dir = os.path.join(output_dir, base_name)
    if not os.path.exists(sprite_output_dir):
        os.makedirs(sprite_output_dir)

    # Load the plist file
    with open(plist_file, "rb") as f:
        plist_data = plistlib.load(f)

    # Load the main image
    main_image = Image.open(png_file)

    # Process each frame
    frames = plist_data["frames"]
    for frame_name, frame_data in frames.items():
        # Get the texture rectangle
        rect_str = frame_data["textureRect"]
        x, y, width, height = parse_rect(rect_str)
        
        # Check if the sprite is rotated
        is_rotated = frame_data["textureRotated"]
        
        # Crop the sprite from the main image
        sprite = main_image.crop((x, y, x + width, y + height))
        
        # Rotate if necessary
        if is_rotated:
            sprite = sprite.rotate(90, expand=True)
        
        # Save the sprite
        output_path = os.path.join(sprite_output_dir, frame_name)
        sprite.save(output_path)
        print(f"Saved {frame_name} to {sprite_output_dir}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 plistcut.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        sys.exit(1)
    
    matching_pairs = find_matching_files(directory)
    if not matching_pairs:
        sys.exit(1)
    
    print(f"Found {len(matching_pairs)} matching plist/png pairs")
    for plist_file, png_file in matching_pairs:
        print(f"\nProcessing {plist_file} and {png_file}")
        process_sprite_sheet(plist_file, png_file, directory)

if __name__ == "__main__":
    main()
