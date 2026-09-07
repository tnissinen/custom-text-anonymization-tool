import torch


def check_torch_gpu(verbose=False):
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