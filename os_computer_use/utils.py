from PIL import ImageDraw
import re
import base64
import io
import fireworks.client
from os_computer_use.llm import osatlas_config


def draw_big_dot(image, coordinates, color="red", radius=12):
    draw = ImageDraw.Draw(image)
    x, y = coordinates
    bounding_box = [x - radius, y - radius, x + radius, y + radius]
    draw.ellipse(bounding_box, fill=color, outline=color)
    return image


def convert_to_base64(image):
    image_format = "JPEG" if image.format == "JPEG" else "PNG"
    mime_type = f"image/{image_format.lower()}"
    buffered = io.BytesIO()
    image.save(buffered, format=image_format)
    return base64.b64encode(buffered.getvalue()).decode("utf-8"), mime_type


def send_bbox_request(image_base64, mime_type, prompt):
    system_prompt = "Respond to the user's query and always respond in the format of: <|box_start|>(x,y),(x,y)<|box_end|>"
    image = [
        {"type": "text", "text": prompt},
        {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{image_base64}"},
        },
    ]
    response = fireworks.client.ChatCompletion.create(
        model=osatlas_config["model"],
        messages=[
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": image},
        ],
    )
    return response.choices[0].message.content


def extract_bbox_midpoint(bbox_response):
    match = re.search(r"<\|box_start\|>(.*?)<\|box_end\|>", bbox_response)
    inner_text = match.group(1) if match else bbox_response
    numbers = [int(num) for num in re.findall(r"\d+", inner_text)]
    if len(numbers) == 2:
        return numbers[0], numbers[1]
    elif len(numbers) >= 4:
        return (numbers[0] + numbers[2]) // 2, (numbers[1] + numbers[3]) // 2
    else:
        return None
