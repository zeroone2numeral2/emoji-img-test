import os
import random


WHITE_CHECKMARK_CODEPOINT = '2705'
RED_CROSS_CODEPOINT = '274c'
WARNING_CODEPOINT = '26a0.fe0f'


def hex_codepoint_to_unicode(hex_codepoint: str):
    return chr(int(hex_codepoint, 16))


def hex_codepoint_to_id(hex_codepoints: list, sep: str = "."):
    return sep.join(hex_codepoints)


class Emoji:
    def __init__(self, codepoints_str, sep="-", compile=True):
        self.origin_str = codepoints_str
        self.codepoints_hex = codepoints_str.lower().split(sep)
        self.codepoints_decimal = []
        self.codepoints_unicode = []
        self._sep = sep
        self.id = hex_codepoint_to_id(self.codepoints_hex)

        if compile:
            self.compile()

    def _check_codepoints_len(self, raise_if_higher_than=1):
        if len(self.codepoints_hex) > raise_if_higher_than:
            raise ValueError(f"too many codepoints ({len(self.codepoints_hex)})")

    @property
    def codepoint_hex(self):
        self._check_codepoints_len()
        return self.codepoints_hex[0]

    @property
    def codepoint_unicode(self):
        self._check_codepoints_len()
        return self.codepoints_unicode[0]

    @property
    def codepoint_decimal(self):
        self._check_codepoints_len()
        return self.codepoints_decimal[0]

    @property
    def unicode(self):
        return "".join(self.codepoints_unicode)

    @property
    def file_name(self):
        return f"{self._sep.join(self.codepoints_hex)}.png"

    def compile(self):
        for codepoint_hex in self.codepoints_hex:
            # unicode_str += "0x{:0>8}".format(code)
            # codepoint_str += f"{codepoint_hex}"

            codepoint_decimal = int(codepoint_hex, 16)
            self.codepoints_decimal.append(codepoint_decimal)

            codepoint_unicode = chr(codepoint_decimal)  # https://stackoverflow.com/a/42840113
            self.codepoints_unicode.append(codepoint_unicode)

    def __str__(self):
        return f"Emoji(codepoints_hex={self.codepoints_hex}, codepoints_decimal={self.codepoints_decimal}, codepoints_unicode={self.codepoints_unicode})"


class EmojiButton(Emoji):
    def __init__(self, *args, correct: bool = False, **kwargs):
        self.already_selected = False  # if the user selected this button
        self.correct = correct  # if the emoji is one of the correct ones (in the image)
        super(EmojiButton, self).__init__(*args, **kwargs)

    @property
    def callback_data(self):
        if self.already_selected and self.correct:
            return f"button:already_solved"
        if self.already_selected and not self.correct:
            return f"button:already_error"

        return f"button:{self.id}"

    @property
    def unicode(self):
        if self.already_selected and self.correct:
            return hex_codepoint_to_unicode(WHITE_CHECKMARK_CODEPOINT)
        if self.already_selected and not self.correct:
            return hex_codepoint_to_unicode(RED_CROSS_CODEPOINT)

        return super(EmojiButton, self).unicode

    @classmethod
    def convert(cls, emoji: Emoji):
        return cls(emoji.origin_str)


class Emojis:
    BLACKLIST = (WHITE_CHECKMARK_CODEPOINT, RED_CROSS_CODEPOINT, WARNING_CODEPOINT)  # do not use these two emojis

    def __init__(self, dir_path="emojis", min_codepoints=1, max_codepoints=999):
        self.min_codepoints = min_codepoints
        self.max_codepoints = max_codepoints
        self.emojis = []

        emojis = [file_name for file_name in os.listdir(dir_path)]
        for file_name in emojis:
            emoji = Emoji(file_name.replace(".png", ""), compile=False)
            if self.min_codepoints <= len(emoji.codepoints_hex) <= self.max_codepoints:
                emoji.compile()
            else:
                continue

            self.emojis.append(emoji)

    def random(self, count=1, min_codepoints=1, max_codepoints=999):
        if count > len(self.emojis):
            raise ValueError(f"number of emojis to return can't be greater than total ({len(self.emojis)})")

        if self.min_codepoints < min_codepoints:
            raise ValueError(f"passed min_codepoints is greater than the original min_codepoints value ({min_codepoints}, {self.min_codepoints})")

        if self.max_codepoints > max_codepoints:
            raise ValueError(f"passed max_codepoints is lower than the original max_codepoints value ({max_codepoints}, {self.max_codepoints})")

        if count == 1:
            return random.choice(self.emojis)

        random_emojis = []
        attempts = 0
        while len(random_emojis) < count:
            attempts += 1
            emoji = random.choice(self.emojis)
            if emoji not in random_emojis and emoji.id not in self.BLACKLIST:
                if min_codepoints <= len(emoji.codepoints_hex) <= max_codepoints:
                    random_emojis.append(emoji)

        return random_emojis


def main():
    emojis = Emojis()
    print(emojis.random())

    print(chr(int('0x1f9b6', 16)))


if __name__ == "__main__":
    main()
