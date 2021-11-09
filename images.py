import logging
import math
import os
from random import randint, choice
from pathlib import Path
from typing import List

from PIL import Image

from emojis import EmojiButton

logger = logging.getLogger(__name__)


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

    logger.debug(f"grid side for {number_of_emojis} emojis: {grid_x}x{grid_y}")

    cell_w = math.floor(img_width / grid_x)
    cell_h = math.floor(img_height / grid_y)
    logger.debug(f"cells side (width: {img_width}): {grid_x} x {cell_w} = {grid_x*cell_w}")
    logger.debug(f"cells side (height: {img_height}): {grid_y} x {cell_h} = {grid_y*cell_h}")

    emoji_w = cell_w - (cell_padding * 2)
    emoji_h = cell_h - (cell_padding * 2)
    logger.debug(f"emojis size: {emoji_w} x {emoji_h}")

    coordinates = []
    for x in range(grid_x):
        for y in range(grid_y):
            offset_x = (cell_w * x) + cell_padding
            offset_y = (cell_h * y) + cell_padding

            logger.debug(f"cell {x}x{y}: {offset_x:3}, {offset_y:3}")

            coordinates.append((offset_x, offset_y))

        # logger.debug("")

    return coordinates, (emoji_w, emoji_h)


class CaptchaImage:
    def __init__(self, background_path="assets/bg.jpg", resize_to=(740, 740), emojis=List[EmojiButton]):
        self.bg_img = Image.open(background_path, 'r').convert('RGBA').resize(resize_to, Image.ANTIALIAS)
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
            new_size = randint(emoji_width, emoji_height)
            png_img = png_img.resize((new_size, new_size), Image.ANTIALIAS)

            self.bg_img.paste(png_img, (x, y), png_img)  # https://stackoverflow.com/a/5324782

        self.bg_img.save(file_path)

        self.result_file_path = file_path
        return file_path

    def delete_generated_image(self):
        try:
            os.remove(self.result_file_path)
        except FileNotFoundError:
            pass

