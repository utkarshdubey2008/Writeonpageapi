from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from urllib.parse import unquote
from PIL import Image, ImageDraw, ImageFont
import io

app = FastAPI()

PAGE_SIZES = {"A4": (1240, 1754), "A5": (874, 1240), "Letter": (1275, 1650)}
PEN_COLORS = {
    "black": (0, 0, 0),
    "red": (220, 20, 60),
    "blue": (25, 25, 112),
    "green": (34, 139, 34)
}

FONTS = {
    "cursive": "fonts/CedarvilleCursive-Regular.ttf",
    "normal": "fonts/Kalam-Regular.ttf"
}

def create_image(page_size, pen_color, text, font_path):
    try:
        width, height = page_size
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path, 50)
        line_spacing = 80
        for y in range(line_spacing, height, line_spacing):
            draw.line((0, y, width, y), fill=(200, 200, 200), width=2)
        margin = 100
        max_width = width - 2 * margin
        y_position = 100
        paragraphs = text.split("\n")
        for paragraph in paragraphs:
            words = paragraph.split(" ")
            line = ""
            for word in words:
                test_line = f"{line} {word}".strip()
                text_bbox = font.getbbox(test_line)
                text_width = text_bbox[2] - text_bbox[0]
                if text_width <= max_width:
                    line = test_line
                else:
                    draw.text((margin, y_position), line, fill=pen_color, font=font)
                    y_position += line_spacing
                    line = word
                    if y_position + line_spacing > height:
                        break
            if line:
                draw.text((margin, y_position), line, fill=pen_color, font=font)
                y_position += line_spacing
            y_position += line_spacing
            if y_position + line_spacing > height:
                break
        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/create/{page_size}/{pen_color}/{font_style}/prompt={text}")
def create_image_api(page_size: str, pen_color: str, font_style: str, text: str):
    try:
        decoded_text = unquote(text)
        if page_size not in PAGE_SIZES:
            raise HTTPException(status_code=400, detail="Invalid page size.")
        if pen_color not in PEN_COLORS:
            raise HTTPException(status_code=400, detail="Invalid pen color.")
        if font_style not in FONTS:
            raise HTTPException(status_code=400, detail="Invalid font style.")
        font_path = FONTS[font_style]
        image = create_image(PAGE_SIZES[page_size], PEN_COLORS[pen_color], decoded_text, font_path)
        byte_io = io.BytesIO()
        image.save(byte_io, "PNG", quality=95)
        byte_io.seek(0)
        return StreamingResponse(byte_io, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
