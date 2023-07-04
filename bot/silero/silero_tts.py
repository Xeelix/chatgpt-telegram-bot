# -*- coding: utf-8 -*-
import os
import re
import subprocess

import torch
import time

import wavio
from num2words import num2words

device = torch.device('cpu')
torch.set_num_threads(4)
local_file = '../model.pt'

sample_rate = 24000
# aidar, baya, kseniya, xenia, eugene, random
speaker = 'xenia'

ffmpeg_path = "ffmpeg"

model = None


def init():
    global model

    if not os.path.isfile(local_file):
        torch.hub.download_url_to_file('https://models.silero.ai/models/tts/ru/v3_1_ru.pt',
                                       local_file)

    print("Initialization...")
    model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    model.to(device)

def split_text(text):
    limit = 500

    if len(text) <= limit:
        return [text]

    parts = []
    while len(text) > limit:
        idx = text.rfind(' ', 0, limit)  # Find the last space character before the 1000th character
        if idx == -1:
            idx = limit
        parts.append(text[:idx].strip())  # Add the substring before the space character to the parts list
        text = text[idx:].strip()  # Update the text to the remaining substring

    parts.append(text)  # Add the last remaining part to the parts list
    return parts


def _nums_to_text(text: str) -> str:
    """
    Преобразует числа в буквы: 1 -> один, 23 -> двадцать три.
    :arg text: str
    :return: str
    """
    return re.sub(
        r"(\d+)",
        lambda x: num2words(int(x.group(0)), lang="ru"),
        text)


def get_enhanced_text(text):
    text = f"<speak>" \
           f"{text}" \
           f"</speak>"

    return text


def get_normalized_text(text):


    text = get_enhanced_text(text)
    # text = text.replace("\n\n", ' <break time="1s" strength="x-weak"/> ')

    text = text.replace('\n', ' ')
    text = text.strip()

    b = 12
    return text


def wav_to_ogg(in_filename: str, out_filename: str = None):
    if not in_filename:
        raise Exception("Укажите путь и имя файла in_filename")

    if out_filename is None:
        out_filename = "../test_1.ogg"

    if os.path.exists(out_filename):
        os.remove(out_filename)

    command = [
        ffmpeg_path,
        "-loglevel", "quiet",
        "-i", in_filename,
        "-acodec", "libopus",
        out_filename
    ]
    proc = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    proc.wait()
    return out_filename


def _get_ogg(text):
    wav_path = generate_wav(text)
    ogg_file = wav_to_ogg(wav_path)
    if os.path.exists(wav_path):
        os.remove(wav_path)

    return ogg_file


def text_to_ogg(text):
    ogg_audio_path = _get_ogg(text)
    return ogg_audio_path


def add_accent(word, morph):
    parsed_word = morph.parse(word)[0]
    accented_word = parsed_word.word.replace(parsed_word.normal_form[-parsed_word.tag.stress:],
                                             '́' + parsed_word.normal_form[parsed_word.tag.stress:])
    return accented_word


def accentuate_text(text, morph):
    words = re.findall(r'\b\w+\b', text)
    accented_words = [add_accent(word, morph) for word in words]
    return re.sub(r'\b\w+\b', lambda match: accented_words.pop(0), text)


def replace_accent_with_plus(text):
    return text.replace('́', '+')


def generate_wav(text, voice_path='old_grandma_1.pt', output_file='test.wav', is_generate_random=False,
                 is_use_prepared=True):
    start_time = time.time()

    if text is None:
        raise Exception("Передайте текст")

        # Удаляем существующий файл чтобы все хорошо работало
    if os.path.exists("test.wav"):
        os.remove("test.wav")

    text = _nums_to_text(text)
    text = get_normalized_text(text)

    print("Generating wav...")
    # audio_path = model.save_wav(text=text,
    #                             speaker=speaker,
    #                             sample_rate=sample_rate,
    #                             put_accent=True,
    #                             put_yo=True)

    # if is_generate_random:

    if is_use_prepared:
        if speaker == "random":
            audio = model.apply_tts(ssml_text=text,
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    voice_path=voice_path,
                                    put_accent=True,
                                    put_yo=True)
        else:
            audio = model.apply_tts(ssml_text=text,
                                    speaker=speaker,
                                    sample_rate=sample_rate,
                                    put_accent=True,
                                    put_yo=True)

    else:
        audio = model.apply_tts(ssml_text=text,
                                speaker=speaker,
                                sample_rate=sample_rate,
                                put_accent=True,
                                put_yo=True)
        model.save_random_voice(voice_path)

    wavio.write(output_file, audio, sample_rate, sampwidth=2)

    print(f"wav generation time: {time.time() - start_time}")

    return output_file

if __name__ == "__main__":
    init()

    text_input = """
О, бля, какая подлянка, даун сука, ты зачем такое предложил? 
"""

    # for i in range(1, 40):
    #     generate_wav(text_input, voice_path=f'{i}_voice.pt', output_file=f'test{i}.wav', is_use_prepared=False)

    generate_wav(text_input, voice_path=f'old_grandma_1.pt', output_file=f'test.wav', is_use_prepared=True)
