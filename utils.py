import torch
import os
from transformers import AutoModelForTokenClassification, AutoTokenizer


def check_torch_gpu(verbose=False):
    """ Check if PyTorch can access a GPU and print the result. If verbose is True, also perform a simple tensor operation on the GPU to verify functionality."""

    try:
        # Check if CUDA is available
        if torch.cuda.is_available():
            print(f"✅ CUDA is available. GPU count: {torch.cuda.device_count()}")
            print(f"Using GPU: {torch.cuda.get_device_name(0)}")

            if verbose:
                # Create a tensor on GPU
                tensor_gpu = torch.rand(3, 3).to("cuda")
                print(f"Tensor device: {tensor_gpu.device}")

                # Verify that operations run on GPU
                result = tensor_gpu @ tensor_gpu  # Matrix multiplication
                print(f"Result device: {result.device}")

        else:
            print("❌ CUDA is NOT available. Running on CPU.")

            if verbose:
                tensor_cpu = torch.rand(3, 3)
                print(f"Tensor device: {tensor_cpu.device}")

    except Exception as e:
        print(f"Error checking GPU: {e}")


def check_model_and_tokenizer(model_name):
    """ Check if the specified model and tokenizer are available locally. If not, download them from Hugging Face and save them to the local directory."""

    folder = os.path.dirname(os.path.realpath(__file__))
    full_path = folder + f"/{model_name}"

    if not os.path.exists(full_path):
        print(f"❌ Model path not found: {full_path}. Downloading {model_name}... (this is only needed at first run)")

        # Download the model and tokenizer from Hugging Face
        model = AutoModelForTokenClassification.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # Save the model and tokenizer to the local directory
        tokenizer.save_pretrained(full_path)
        model.save_pretrained(full_path)
        print("Model downloaded and saved.")
    else:
        print(f"✅ Model {full_path} is available.")