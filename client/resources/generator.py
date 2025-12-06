from random import randint
from PIL import Image

def _main():
    # frame_colors = [
            # [0x45, 0x68, 0x82],
            # # [0xE3, 0xE3, 0xE3],
            # ]
    # colors = [
            # [0x1B, 0x3C, 0x53],
            # [0x23, 0x4C, 0x6A],
            # ]
    frame_colors = [

            #73432C
            [0x73, 0x43, 0x2C],
            [0x7F, 0x76, 0x4D],
            #6C503A
            [0x6C, 0x50, 0x3A],
            ]
    dark_scale = 0.5
    colors = [
            #593D27
            [int(0x59*dark_scale),
             int(0x3D*dark_scale),
             int(0x27*dark_scale)],
            #63452D
            [int(0x63*dark_scale),
             int(0x45*dark_scale),
             int(0x2D*dark_scale)],
            #583C26
            [int(0x58*dark_scale),
             int(0x3C*dark_scale),
             int(0x26*dark_scale)],
            ]
    counter = 0
    for fill_color in colors:
        for frame_color in frame_colors:
            for i in range(4):
                width = height = 150

                pixels = []
                for y in range(height):
                    pixels.append(list())
                    for x in range(width):
                        pixels[y].append(list())

                thickness = 5

                for y in range(height):
                    for x in range(width):
                        pixels[y][x] = fill_color

                # frame
                if i == 0:
                    for y in range(height):
                        for i in range(thickness):
                            pixels[y][i] = frame_color
                            # pixels[y][(i+1) * -1] = frame_color
                    for i in range(thickness):
                        for x in range(width):
                            pixels[i][x] = frame_color
                            # pixels[(i+1) * -1][x] = frame_color
                if i == 1:
                    for y in range(height):
                        for i in range(thickness):
                            pixels[y][i] = frame_color
                            # pixels[y][(i+1) * -1] = frame_color
                    for i in range(thickness):
                        for x in range(width):
                            # pixels[i][x] = frame_color
                            pixels[(i+1) * -1][x] = frame_color
                if i == 2:
                    for y in range(height):
                        for i in range(thickness):
                            # pixels[y][i] = frame_color
                            pixels[y][(i+1) * -1] = frame_color
                    for i in range(thickness):
                        for x in range(width):
                            # pixels[i][x] = frame_color
                            pixels[(i+1) * -1][x] = frame_color
                if i == 3:
                    for y in range(height):
                        for i in range(thickness):
                            # pixels[y][i] = frame_color
                            pixels[y][(i+1) * -1] = frame_color
                    for i in range(thickness):
                        for x in range(width):
                            pixels[i][x] = frame_color
                            # pixels[(i+1) * -1][x] = frame_color



                # _x = randint(0, width)
                # _y = randint(0, height)
                # _height = randint(0, int(height/2))
                # if _y + _height > height: _height = height - _y
                # _width = randint(0, int(width/2))
                # if _x + _width > width: _width = width - _x
                # _color = colors[randint(0, len(colors) - 1)]

                # for y in range(_height):
                    # for x in range(_width):
                        # pixels[_y + y][_x + x] = _color

                # write to file
                raw_pixels = []
                for y in range(height):
                    for x in range(width):
                        raw_pixels.extend(pixels[y][x])

                random_image = Image.frombytes('RGB', (width, height), bytes(raw_pixels))
                random_image.save(f"tile{counter:01}.jpg")
                counter += 1

def generate(name, fill, frame, frame_thickness=5):
    width = height = 150

    pixels = []
    for y in range(height):
        pixels.append(list())
        for x in range(width):
            pixels[y].append(list())

    for y in range(height):
        for x in range(width):
            pixels[y][x] = fill

    for y in range(height):
        for i in range(frame_thickness):
            pixels[y][i] = frame
            pixels[y][(i+1) * -1] = frame
    for i in range(frame_thickness):
        for x in range(width):
            pixels[i][x] = frame
            pixels[(i+1) * -1][x] = frame

    # write to file
    raw_pixels = []
    for y in range(height):
        for x in range(width):
            raw_pixels.extend(pixels[y][x])

    random_image = Image.frombytes('RGB', (width, height), bytes(raw_pixels))
    random_image.save(f"{name}.jpg")

if __name__=='__main__':
    generate('water', [0x23, 0x4C, 0x6A], [0x45, 0x68, 0x82])

    # generate('floor', [0x37, 0x1d, 0x10], [0x23, 0x17, 0x09])
    generate('floor', [0x37, 0x1d, 0x10], [0x6F, 0x4F, 0x1D], frame_thickness=2)

