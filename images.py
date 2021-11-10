import logging
import math
import os
from random import randint, choice
from pathlib import Path
from typing import List

from PIL import Image

from emojis import EmojiButton

logger = logging.getLogger(__name__)
logger_geom = logging.getLogger("geometry")


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

    logger_geom.debug(f"grid size for {number_of_emojis} emojis: {grid_x}x{grid_y}")

    cell_w = math.floor(img_width / grid_x)
    cell_h = math.floor(img_height / grid_y)
    logger_geom.debug(f"cells side (width: {img_width}): {grid_x} x {cell_w} = {grid_x*cell_w}")
    logger_geom.debug(f"cells side (height: {img_height}): {grid_y} x {cell_h} = {grid_y*cell_h}")

    emoji_w = cell_w - (cell_padding * 2)
    emoji_h = cell_h - (cell_padding * 2)
    logger_geom.debug(f"emojis size: {emoji_w} x {emoji_h}")

    coordinates = []
    for x in range(grid_x):
        for y in range(grid_y):
            offset_x = (cell_w * x) + cell_padding
            offset_y = (cell_h * y) + cell_padding

            logger_geom.debug(f"cell {x+1}x{y+1}: {offset_x:3}, {offset_y:3}")

            coordinates.append((offset_x, offset_y))

        # logger.debug("")

    return coordinates, (emoji_w, emoji_h)


class CaptchaImage:
    def __init__(self, background_path, emojis=List[EmojiButton], scale_factor=0, max_side=0):
        self.bg_img = Image.open(background_path, 'r').convert('RGBA')

        resize_to = None
        if max_side:
            size = self.bg_img.size
            largest_side = size[0] if size[0] > size[1] else size[1]

            logger.debug("max side: %d, largest side: %d", max_side, largest_side)

            if largest_side <= max_side:
                resize_to = size
            else:
                rateo = round(max_side / largest_side, 4)
                resize_to = (int(size[0] * rateo), int(size[1] * rateo))
        if scale_factor:
            size = self.bg_img.size
            resize_to = (int(size[0] * scale_factor), int(size[1] * scale_factor))

        if resize_to:
            logger.debug('resizing to: %s', resize_to)
            self.bg_img = self.bg_img.resize(resize_to, Image.ANTIALIAS)

        self.png_files_path = []
        self.result_file_path = None

        for emoji in emojis:
            png_image_path = Path("emojis/") / emoji.file_name
            self.png_files_path.append(png_image_path)

        self.number_of_emojis = len(emojis)

    def generate_capctha_image(self, file_path):
        bg_w, bg_h = self.bg_img.size
        coordinates, (emoji_width, emoji_height) = gen_offsets_grid(
            bg_w, bg_h,
            number_of_emojis=self.number_of_emojis,
            cell_padding=10
        )

        for i, (x, y) in enumerate(coordinates):
            if i + 1 > self.number_of_emojis:
                # the number of available coordinates in the list might be higher than the number of emojis,
                # because we generate coordinates for every grid cell (even the empty ones)
                break

            png_image_path = self.png_files_path[i]
            png_img = Image.open(png_image_path).convert('RGBA')

            # rotate emoji
            # rotation might cause the emojis to slightly overlap in the grid, but shouldn't be an issue
            rotations = (randint(20, 90), randint(290, 360))
            png_img = png_img.rotate(choice(rotations))

            # resize emoji
            new_emoji_size = randint(
                # make sure to pass the smaller first
                emoji_width if emoji_width <= emoji_height else emoji_height,
                emoji_width if emoji_width > emoji_height else emoji_height,
            )
            png_img = png_img.resize((new_emoji_size, new_emoji_size), Image.ANTIALIAS)

            self.bg_img.paste(png_img, (x, y), png_img)  # https://stackoverflow.com/a/5324782

        self.bg_img.save(file_path)

        self.result_file_path = file_path
        return file_path

    def delete_generated_image(self):
        try:
            os.remove(self.result_file_path)
        except FileNotFoundError:
            pass

