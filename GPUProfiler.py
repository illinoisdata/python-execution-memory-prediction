import torch
import tensorflow as tf
from contextlib import contextmanager


@contextmanager
def gpu_profiler(type=None):
    if type is None or type == "None":
        yield
        return

    if type == "torch":
        if not torch.cuda.is_available():
            print(
                f"peak gpu: 0 MB, gpu increment: 0 MB")
            yield
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
    elif type == "tensorflow":
        if not tf.config.list_physical_devices('GPU'):
            print(
                f"peak gpu: 0 MB, gpu increment: 0 MB")
            yield
            return

        device = 'GPU:0'
        tf.config.experimental.reset_memory_stats(device)
        start_alloc = tf.config.experimental.get_memory_info(device)['current']

        yield

        end_alloc = tf.config.experimental.get_memory_info(device)['current']
        peak_alloc = tf.config.experimental.get_memory_info(device)['peak']

        print(
            f"peak gpu: {peak_alloc/1e6:.4f} MB, gpu increment: {(peak_alloc - start_alloc)/1e6:.4f} MB")
    else:
        yield
