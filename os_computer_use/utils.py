from PIL import ImageDraw
import re
from os_computer_use.llm import osatlas_config
from gradio_client import Client

osatlas = Client(osatlas_config["source"])


def draw_big_dot(image, coordinates, color="red", radius=12):
    draw = ImageDraw.Draw(image)
    x, y = coordinates
    bounding_box = [x - radius, y - radius, x + radius, y + radius]
    draw.ellipse(bounding_box, fill=color, outline=color)
    return image


def send_bbox_request(image_data, prompt):
    try:
        result = osatlas.predict(
            image=image_data,
            text_input=prompt + "\nReturn the response in the form of a bbox",
            model_id=osatlas_config["model"],
            api_name=osatlas_config["api_name"],
        )
        midpoint = extract_bbox_midpoint(result[1])
        print("BBOX: " + result[2])
        if not midpoint:
            raise ValueError("The bbox response is malformed.")
        return midpoint
    except Exception as e:
        return None


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
