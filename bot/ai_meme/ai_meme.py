import asyncio
import base64
import logging
import random
import re
import string

import aiohttp
from fake_useragent import UserAgent
from PIL import Image, ImageDraw, ImageFont


class AiMeme:
    def __init__(self):
        self.user_agent = UserAgent()
        self.headers = self.__get_headers()

    def __get_headers(self):
        headers = {
            'Accept': 'image/avif,image/webp,*/*',
            'User-Agent': self.user_agent.random
        }
        return headers

    async def fetch_html(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as response:
                return await response.text()

    def image_to_data_url(self, image_path):
        # Open the image file in binary mode
        with open(image_path, "rb") as image_file:
            # Read the image data and base64-encode it
            encoded_data = base64.b64encode(image_file.read()).decode()
            # Create the Data URL string
            data_url = f"data:image/jpeg;base64,{encoded_data}"
            return data_url

    # async def request_ai_meme(self, image_data):
    #     async with aiohttp.ClientSession() as session:
    #         async with session.post('https://ai-meme.com/api', headers=self.headers,
    #                                 json={"image": image_data, "lang": "ru"}) as response:
    #             return await response.json()

    def generate_random_hash(self, length):
        characters = string.ascii_letters + string.digits
        random_hash = ''.join(random.choice(characters) for _ in range(length))
        return random_hash

    async def send_image_request(self, image_data):
        url = "https://salesforce-blip.hf.space/api/queue/push/"
        payload = {
            "fn_index": 0,
            "data": [
                image_data,
                "Image Captioning",
                "None",
                "Nucleus sampling",
            ],
            "action": "predict",
            "session_hash": self.generate_random_hash(10),
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                return await response.json()

    async def check_status(self, hash):
        url = f"https://salesforce-blip.hf.space/api/queue/status/"
        payload = {"hash": hash}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=self.headers) as response:
                return await response.json()

    # Paste text on image
    def paste_text_on_image(self, image_path, text):
        pass

    async def generate_meme(self, image_path):
        image_data = self.image_to_data_url(image_path)

        response = await self.send_image_request(image_data)
        hash = response["hash"]

        while True:
            status_response = await self.check_status(hash)
            if status_response["status"] == "COMPLETE":
                caption = status_response["data"]["data"][0]
                logging.debug(f"Image description: {caption}")
                return caption
            logging.debug(f"Image not yet processed... {status_response}")
            await asyncio.sleep(1)


def wrap_text(text, font, max_width):
    lines = []
    words = text.split()
    current_line = []

    for word in words:
        current_line.append(word)
        line_width = font.getlength(" ".join(current_line))
        if line_width > max_width:
            current_line.pop()
            lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines


def embed_text_on_image(image_path, text, output_image_path, font_path="./utils_files/impact.ttf"):
    # Load image
    image = Image.open(image_path)
    width, height = image.size

    # Set up font
    font_size = int(height * 0.05)
    font = ImageFont.truetype(font_path, font_size)

    # Set up drawing context
    draw = ImageDraw.Draw(image)

    # Wrap text into multiple lines if necessary
    max_text_width = int(width * 0.9)
    lines = wrap_text(text, font, max_text_width)
    line_height = font.getbbox("A")[3] - font.getbbox("A")[1]

    # Calculate position for the text
    total_text_height = len(lines) * line_height
    x = (width - max_text_width) / 2
    y = height - total_text_height - 20

    # Draw text with outline
    outline_color = (0, 0, 0)
    fill_color = (255, 255, 255)
    outline_thickness = 2

    for line in lines:
        line_width = font.getlength(line)
        line_x = x + (max_text_width - line_width) / 2
        for move_x in range(-outline_thickness, outline_thickness + 1):
            for move_y in range(-outline_thickness, outline_thickness + 1):
                draw.text((line_x + move_x, y + move_y), line, font=font, fill=outline_color)
        draw.text((line_x, y), line, font=font, fill=fill_color)
        y += line_height

    # Save output image
    image.save(output_image_path)


def extract_russian_text(text):
    russian_string = re.sub(r'[^а-яА-ЯёЁ0-9\s\.,!?:;—\-«»]+', '', text)
    russian_string = russian_string.strip()
    if russian_string:
        text = russian_string

    return text


async def main():
    ai_meme = AiMeme()

    result = await ai_meme.generate_meme("ai_original.jpg", "ai_original_gen.jpg")
    print(result)
    # generated_text = result['text']
    #
    # # Extract only russian textt
    # generated_text = extract_russian_text(generated_text)
    #
    # embed_text_on_image("ai_original.jpg", generated_text, "ai_meme.jpg")
    # print(f"Prepared result: {generated_text}")


if __name__ == "__main__":
    asyncio.run(main())
