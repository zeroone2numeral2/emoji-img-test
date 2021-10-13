import os
from random import randint, choice
from pathlib import Path

from PIL import Image


emojis = [file_name for file_name in os.listdir("emojis")]

background_img = Image.open('bg.jpg', 'r').convert('RGBA').resize((740, 740), Image.ANTIALIAS)


def gen_offset(max_width: int, max_height: int, existing_offsets: list):
    offset = ()

    # avoid emojis overlapping
    while not offset:
        offset_w = randint(0, max_width)
        offset_h = randint(0, max_height)
        print(f"\nCANDIDATE: {offset_w}, {offset_h}")

        if not existing_offsets:
            return (offset_w, offset_h)

        valid = True
        for existing_offset_w, existing_offset_h in existing_offsets:
            threshold = 150

            w_bound_lower = existing_offset_w - threshold
            w_bound_higher = existing_offset_w + threshold

            h_bound_lower = existing_offset_h - threshold
            h_bound_higher = existing_offset_h + threshold

            print("", f"testing bounds: {w_bound_lower}-{w_bound_higher}, {h_bound_lower}-{h_bound_higher}")

            if (w_bound_lower < offset_w < w_bound_higher) and (h_bound_lower < offset_h < h_bound_higher):
                print("",
                      f"DISCARDED offset: ({offset_w}, {offset_h}): too close to ({existing_offset_w}, {existing_offset_h})")
                valid = False
                break

        if valid:
            offset = (offset_w, offset_h)
            print("", f"offset OK: ({offset_w}, {offset_h})")

            return offset


def main():
    png_image_path = Path("emojis/") / choice(emojis)
    png_img = Image.open(png_image_path).convert('RGBA')
    png_img = png_img.rotate(randint(0, 180))

    print(background_img.size)
    print(png_img.size)

    bg_w, bg_h = background_img.size
    existing_offsets = []
    candidate_offsets_count = 0
    for i in range(5):
        png_image_path = Path("emojis/") / choice(emojis)
        png_img = Image.open(png_image_path).convert('RGBA')

        # rotate emoji
        rotations = (randint(20, 90), randint(290, 360))
        png_img = png_img.rotate(choice(rotations))

        # resize emoji
        new_size = randint(150, 200)
        png_img = png_img.resize((new_size, new_size), Image.ANTIALIAS)

        # calculate pasting offset
        max_width = bg_w - new_size
        max_height = bg_h - new_size

        offset = gen_offset(max_width, max_height, existing_offsets)
        existing_offsets.append(offset)

        background_img.paste(png_img, offset, png_img)  # https://stackoverflow.com/a/5324782

    background_img.save('result.png')


if __name__ == "__main__":
    main()
