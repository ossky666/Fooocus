import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

import sys
import platform
import fooocus_version

from modules.launch_util import is_installed, run, python, \
    run_pip, repo_dir, git_clone, requirements_met, script_path, dir_repos
from modules.model_loader import load_file_from_url
from modules.path import modelfile_path, lorafile_path, vae_approx_path, fooocus_expansion_path, upscale_models_path

REINSTALL_ALL = False

def prepare_environment():
    torch_index_url = os.environ.get('TORCH_INDEX_URL', "https://download.pytorch.org/whl/cu118")
    torch_command = os.environ.get('TORCH_COMMAND',
                                   f"pip install torch==2.0.1 torchvision==0.15.2 --extra-index-url {torch_index_url}")
    requirements_file = os.environ.get('REQS_FILE', "requirements_versions.txt")

    xformers_package = os.environ.get('XFORMERS_PACKAGE', 'xformers==0.0.20')

    comfy_repo = os.environ.get('COMFY_REPO', "https://github.com/lllyasviel/ComfyUI_2bc12d.git")
    comfy_commit_hash = os.environ.get('COMFY_COMMIT_HASH', "2bc12d3d22efb5c63ae3a7fc342bb2dd16b31735")

    print(f"Python {sys.version}")
    print(f"Fooocus version: {fooocus_version.version}")

    comfyui_name = 'ComfyUI-from-StabilityAI-Official'
    git_clone(comfy_repo, repo_dir(comfyui_name), "Inference Engine", comfy_commit_hash)
    sys.path.append(os.path.join(script_path, dir_repos, comfyui_name))

    if REINSTALL_ALL or not is_installed("torch") or not is_installed("torchvision"):
        run(f'"{python}" -m {torch_command}', "Installing torch and torchvision", "Couldn't install torch", live=True)

    if REINSTALL_ALL or not is_installed("xformers"):
        if platform.system() == "Windows":
            if platform.python_version().startswith("3.10"):
                run_pip(f"install -U -I --no-deps {xformers_package}", "xformers", live=True)
            else:
                print("Installation of xformers is not supported in this version of Python.")
                print(
                    "You can also check this and build manually: https://github.com/AUTOMATIC1111/stable-diffusion-webui/wiki/Xformers#building-xformers-on-windows-by-duckness")
                if not is_installed("xformers"):
                    exit(0)
        elif platform.system() == "Linux":
            run_pip(f"install -U -I --no-deps {xformers_package}", "xformers")

    if REINSTALL_ALL or not requirements_met(requirements_file):
        run_pip(f"install -r \"{requirements_file}\"", "requirements")

    return


model_filenames = [
    ('sdxl10ArienmixxlAsian_v20.safetensors',
     'https://civitai-delivery-worker-prod-2023-09-01.5ac0637cfd0766c97916cefa3764fbdf.r2.cloudflarestorage.com/model/1353487/arienmixxlE4BA9AE6B4B2E4.9jDy.safetensors?X-Amz-Expires=86400&response-content-disposition=attachment%3B%20filename%3D%22sdxl10ArienmixxlAsian_v20.safetensors%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=2fea663d76bd24a496545da373d610fc/20230921/us-east-1/s3/aws4_request&X-Amz-Date=20230921T074526Z&X-Amz-SignedHeaders=host&X-Amz-Signature=7848ef57e2f5a926bcce37ccf690a43fbe833d09dcb28a3a2a3f077d4644c7d9'),
    ('SDXLRonghua_v20.safetensors',
     'https://civitai-delivery-worker-prod-2023-09-01.5ac0637cfd0766c97916cefa3764fbdf.r2.cloudflarestorage.com/model/118828/ronghuaV20.aXbE.safetensors?X-Amz-Expires=86400&response-content-disposition=attachment%3B%20filename%3D%22SDXLRonghua_v20.safetensors%22&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=2fea663d76bd24a496545da373d610fc/20230921/us-east-1/s3/aws4_request&X-Amz-Date=20230921T074239Z&X-Amz-SignedHeaders=host&X-Amz-Signature=b36c546dc31c376cbfe99f76eb629449c599bf108138c4fd99e3bc99c4e1cee3')
]

lora_filenames = [
    ('sd_xl_offset_example-lora_1.0.safetensors',
     'https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_offset_example-lora_1.0.safetensors')
]

vae_approx_filenames = [
    ('xlvaeapp.pth',
     'https://huggingface.co/lllyasviel/misc/resolve/main/xlvaeapp.pth')
]


upscaler_filenames = [
    ('fooocus_upscaler_s409985e5.bin',
     'https://huggingface.co/lllyasviel/misc/resolve/main/fooocus_upscaler_s409985e5.bin')
]


def download_models():
    for file_name, url in model_filenames:
        load_file_from_url(url=url, model_dir=modelfile_path, file_name=file_name)
    for file_name, url in lora_filenames:
        load_file_from_url(url=url, model_dir=lorafile_path, file_name=file_name)
    for file_name, url in vae_approx_filenames:
        load_file_from_url(url=url, model_dir=vae_approx_path, file_name=file_name)
    for file_name, url in upscaler_filenames:
        load_file_from_url(url=url, model_dir=upscale_models_path, file_name=file_name)

    load_file_from_url(
        url='https://huggingface.co/lllyasviel/misc/resolve/main/fooocus_expansion.bin',
        model_dir=fooocus_expansion_path,
        file_name='pytorch_model.bin'
    )

    return


def clear_comfy_args():
    argv = sys.argv
    sys.argv = [sys.argv[0]]
    from comfy.cli_args import args as comfy_args
    comfy_args.disable_cuda_malloc = True
    sys.argv = argv


def cuda_malloc():
    import cuda_malloc


prepare_environment()

clear_comfy_args()
# cuda_malloc()

download_models()

from webui import *
