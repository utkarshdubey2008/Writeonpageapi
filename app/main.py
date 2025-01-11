from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from urllib.parse import unquote
from PIL import Image, ImageDraw, ImageFont
import io

app = FastAPI()

# Predefined Page Sizes and Colors
PAGE_SIZES = {"A4": (1240, 1754), "A5": (874, 1240), "Letter": (1275, 1650)}  # High resolution for good quality
PEN_COLORS = {
    "black": (0, 0, 0),
    "red": (220, 20, 60),
    "blue": (25, 25, 112),
    "green": (34, 139, 34)
}

# Available Fonts
FONTS = {
    "cursive": "fonts/CedarvilleCursive-Regular.ttf",
    "normal": "fonts/Kalam-Regular.ttf",
    "sansita": "fonts/Sansita-Regular.ttf"  # New font added
}

# Function to create an image with the given parameters
def create_image(page_size, pen_color, text, font_path):
    try:
        width, height = page_size
        image = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(font_path, 50)  # Set default font size to 50

        # Line Spacing and Margins
        line_spacing = 70  # Adjust this for spacing between lines
        margin = 100
        max_width = width - 2 * margin
        y_position = 100  # Start writing below the top margin

        # Split text into paragraphs and handle word wrapping
        paragraphs = text.split("\n")
        for paragraph in paragraphs:
            words = paragraph.split(" ")
            line = ""
            for word in words:
                # Check if adding the next word exceeds the maximum width
                test_line = f"{line} {word}".strip()
                text_width = font.getlength(test_line)
                if text_width <= max_width:
                    line = test_line
                else:
                    # Draw the current line and start a new one
                    draw.text((margin, y_position), line, fill=pen_color, font=font)
                    y_position += line_spacing
                    line = word

                    # Check if we've reached the bottom of the page
                    if y_position + line_spacing > height:
                        raise HTTPException(status_code=400, detail="Text exceeds page size")

            # Draw any remaining text in the current line
            if line:
                draw.text((margin, y_position), line, fill=pen_color, font=font)
                y_position += line_spacing

            # Add extra spacing between paragraphs
            y_position += line_spacing

            # Check if we've reached the bottom of the page
            if y_position + line_spacing > height:
                raise HTTPException(status_code=400, detail="Text exceeds page size")

        return image
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# API Endpoint
@app.get("/create/{page_size}/{pen_color}/{font_style}/prompt={text}")
def create_image_api(page_size: str, pen_color: str, font_style: str, text: str):
    try:
        # Decode URL-encoded text
        decoded_text = unquote(text)

        # Validate inputs
        if page_size not in PAGE_SIZES:
            raise HTTPException(status_code=400, detail="Invalid page size. Choose from A4, A5, or Letter.")
        if pen_color not in PEN_COLORS:
            raise HTTPException(status_code=400, detail="Invalid pen color. Choose from black, red, blue, or green.")
        if font_style not in FONTS:
            raise HTTPException(status_code=400, detail="Invalid font style. Choose from cursive, normal, or sansita.")

        # Get the font path based on font style
        font_path = FONTS[font_style]

        # Create the image
        image = create_image(PAGE_SIZES[page_size], PEN_COLORS[pen_color], decoded_text, font_path)

        # Return the image as a response
        byte_io = io.BytesIO()
        image.save(byte_io, "PNG", quality=95)  # High quality for better output
        byte_io.seek(0)
        return StreamingResponse(byte_io, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
