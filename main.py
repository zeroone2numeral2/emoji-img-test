import math
import os
from random import randint, choice
from pathlib import Path

from PIL import Image


emojis = [file_name for file_name in os.listdir("emojis")]

background_img = Image.open('bg.jpg', 'r').convert('RGBA').resize((740, 740), Image.ANTIALIAS)


class Modes:
    RANDOM_POSITION = 1
    GRID = 2


MODE = 2


def gen_offsets_grid(img_width: int, img_height: int, number_of_emojis: int, cell_padding: int = 10):
    grid_x, grid_y = 1, 1
    while True:
        if grid_x * grid_y >= number_of_emojis:
            break
        else:
            if grid_x <= grid_y:
                grid_x += 1
            else:
                grid_y += 1

    print(f"grid side for {number_of_emojis} emojis: {grid_x}x{grid_y}")

    cell_w = math.floor(img_width / grid_x)
    cell_h = math.floor(img_height / grid_y)
    print(f"cells side (width: {img_width}): {grid_x} x {cell_w} = {grid_x*cell_w}")
    print(f"cells side (height: {img_height}): {grid_y} x {cell_h} = {grid_y*cell_h}")

    emoji_w = cell_w - (cell_padding * 2)
    emoji_h = cell_h - (cell_padding * 2)
    print(f"emojis size: {emoji_w} x {emoji_h}")

    coordinates = []
    for x in range(grid_x):
        for y in range(grid_y):
            offset_x = (cell_w * x) + cell_padding
            offset_y = (cell_h * y) + cell_padding

            print(f"cell {x}x{y}: {offset_x:3}, {offset_y:3}")

            coordinates.append((offset_x, offset_y))

        print("\n", end="")

    return coordinates, (emoji_w, emoji_h)


def gen_offset(max_width: int, max_height: int, existing_offsets: list):
    offset = ()

    # avoid emojis overlapping
    while not offset:
        offset_w = randint(0, max_width)
        offset_h = randint(0, max_height)
        print(f"\nCANDIDATE: {offset_w}, {offset_h}")

        if not existing_offsets:
            return offset_w, offset_h

        valid = True
        for existing_offset_w, existing_offset_h in existing_offsets:
            threshold = 150

            w_bound_lower = existing_offset_w - threshold
            w_bound_higher = existing_offset_w + threshold

            h_bound_lower = existing_offset_h - threshold
            h_bound_higher = existing_offset_h + threshold

            print("", f"testing bounds: {w_bound_lower}-{w_bound_higher}, {h_bound_lower}-{h_bound_higher}")

            if (w_bound_lower < offset_w < w_bound_higher) and (h_bound_lower < offset_h < h_bound_higher):
                print("", f"DISCARDED offset: ({offset_w}, {offset_h}): too close to ({existing_offset_w}, {existing_offset_h})")
                valid = False
                break

        if valid:
            offset = (offset_w, offset_h)
            print("", f"offset OK: ({offset_w}, {offset_h})")

            return offset


def gen_offsets_random(img_width: int, img_height: int, number_of_emojis: int):
    new_size = randint(150, 200)

    coordinates = []
    for i in range(number_of_emojis):
        # calculate pasting offset
        max_width = img_width - new_size
        max_height = img_height - new_size

        offset = gen_offset(max_width, max_height, coordinates)
        coordinates.append(offset)

    return coordinates, (new_size, new_size)


def main():
    png_image_path = Path("emojis/") / choice(emojis)
    png_img = Image.open(png_image_path).convert('RGBA')
    png_img = png_img.rotate(randint(0, 180))

    print(background_img.size)
    print(png_img.size)

    bg_w, bg_h = background_img.size

    number_of_emojis = 6

    if MODE == Modes.RANDOM_POSITION:
        coordinates, (emoji_width, emoji_height) = gen_offsets_random(
            bg_w, bg_h,
            number_of_emojis=number_of_emojis,
        )
    elif MODE == Modes.GRID:
        coordinates, (emoji_width, emoji_height) = gen_offsets_grid(
            bg_w, bg_h,
            number_of_emojis=number_of_emojis,
            cell_padding=10
        )
    else:
        raise ValueError(f"invalid mode: {MODE}")

    for i, (x, y) in enumerate(coordinates):
        if i + 1 > number_of_emojis:
            break

        png_image_path = Path("emojis/") / choice(emojis)
        png_img = Image.open(png_image_path).convert('RGBA')

        # rotate emoji
        # rotation might cause the emojis to slightly overlap in the grid, but shouldn't be an issue
        rotations = (randint(20, 90), randint(290, 360))
        png_img = png_img.rotate(choice(rotations))

        # resize emoji
        new_size = randint(emoji_width, emoji_height)
        png_img = png_img.resize((new_size, new_size), Image.ANTIALIAS)

        background_img.paste(png_img, (x, y), png_img)  # https://stackoverflow.com/a/5324782

    background_img.save('result.png')


if __name__ == "__main__":
    main()
    # gen_offsets_grid(812, 812, 6)
