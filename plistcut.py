import plistlib
import os
from PIL import Image
import re

def parse_rect(rect_str):
    # Parse string like "{{1560,430},{219,219}}" into coordinates and size
    match = re.match(r'{{(\d+),(\d+)},{(\d+),(\d+)}}', rect_str)
    if match:
        x, y, width, height = map(int, match.groups())
        return (x, y, width, height)
    return None

def main():
    # Create output directory if it doesn't exist
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Load the plist file
    with open("res/zwFish.plist", "rb") as f:
        plist_data = plistlib.load(f)

    # Load the main image
    main_image = Image.open("res/zwFish.png")

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
        output_path = os.path.join(output_dir, frame_name)
        sprite.save(output_path)
        print(f"Saved {frame_name}")

if __name__ == "__main__":
    main()
