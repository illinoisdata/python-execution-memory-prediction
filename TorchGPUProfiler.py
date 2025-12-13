import torch
from contextlib import contextmanager


@contextmanager
def gpu_profiler():
    if not torch.cuda.is_available():
        print("CUDA not available")
        yield None
        return

    device = torch.cuda.current_device()
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats(device)

    start_alloc = torch.cuda.memory_allocated(device)

    yield

    torch.cuda.synchronize()
    peak_alloc = torch.cuda.max_memory_allocated(device)
    end_alloc = torch.cuda.memory_allocated(device)

    print(
        f"peak gpu: {peak_alloc/1e6:.4f} MB, gpu increment: {(peak_alloc - start_alloc)/1e6:.4f} MB")
