import torch
from ultralytics.utils.torch_utils import select_device


def test_ultralytics_auto_device_detects_cuda():
    assert torch.version.cuda is not None
    assert torch.cuda.is_available()
    device = select_device("", verbose=False)
    assert device.type == "cuda"
    assert device.index == torch.cuda.current_device()
    assert torch.cuda.get_device_name(device)
