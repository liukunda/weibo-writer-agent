import os
import torch
import soundfile as sf
from diffusers import StableAudioPipeline
from dotenv import load_dotenv

load_dotenv()

model_name = "stabilityai/stable-audio-open-1.0"
base_model_dir = os.getenv("BASE_MODEL_DIR")
model_path = os.path.join(base_model_dir, model_name)
curr_dir = os.path.dirname(os.path.abspath(__file__))
output_file_dir = os.path.join(curr_dir, "files")
if not os.path.exists(output_file_dir):
    os.makedirs(output_file_dir, exist_ok=True)
print('model_path: {}'.format(model_path))

pipe = StableAudioPipeline.from_pretrained(model_path, torch_dtype=torch.float16)
pipe = pipe.to("cuda")

# set the seed for generator
generator = torch.Generator("cuda").manual_seed(0)


def inf(prompt, negative_prompt, audio_end_in_s, filename):
    # run the generation
    audio = pipe(
        prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=200,
        audio_end_in_s=audio_end_in_s,
        num_waveforms_per_prompt=3,
        generator=generator,
    ).audios

    output = audio[0].T.float().cpu().numpy()

    output_file = '{}/{}.wav'.format(output_file_dir, filename)

    sf.write(output_file, output, pipe.vae.sampling_rate)

    return output_file


def run():
    # define the prompts
    # prompt = "The sound of a hammer hitting a wooden surface."
    prompt = "128 BPM tech house drum loop."
    # prompt = "A gentle piano melody suitable for a wedding ceremony."
    # prompt = "Imagine the rhythmic clinking of a ship's rigging as it sails through uncharted waters."
    # prompt = "The serene lullaby of waves gently caressing the wooden hull, a timeless melody of adventure and discovery."

    negative_prompt = "Low quality."

    audio_end_in_s = 10.0

    filename = 'demo'

    output_file = inf(prompt, negative_prompt, audio_end_in_s, filename)
    print('output_file: {}'.format(output_file))


if __name__ == '__main__':
    import time

    time1 = time.time()

    run()

    time2 = time.time()

    print(f'total time: {time2 - time1}')
