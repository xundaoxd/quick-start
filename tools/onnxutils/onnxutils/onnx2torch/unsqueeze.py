import torch
from torch import nn


from onnxutils.common import OnnxModel, OnnxNode

from .registry import converter
from .utils import OnnxToTorchModule, OperationConverterResult, OnnxMapping


class TorchUnsqueeze(nn.Module, OnnxToTorchModule):
    def __init__(self, axis):
        super().__init__()
        self.axis = axis

    def forward(self, x):
        return torch.unsqueeze(x, self.axis)


class TorchReshape(nn.Module, OnnxToTorchModule):
    def __init__(self, shape):
        super().__init__()
        self.shape = shape

    def forward(self, x):
        return torch.reshape(x, self.shape)


@converter(operation_type='Unsqueeze', version=13)
def _(onnx_node: OnnxNode, onnx_model: OnnxModel) -> OperationConverterResult:
    axis = onnx_model.get_initializer_by_name(
        onnx_node.inputs()[1]).to_numpy()
    if axis.size == 1:
        axis = int(axis)

        return OperationConverterResult(
            torch_module=TorchUnsqueeze(axis),
            onnx_mapping=OnnxMapping(
                inputs=onnx_node.inputs()[:1],
                outputs=onnx_node.outputs(),
            ),
        )

    vinfo = onnx_model.get_vinfo_by_name(onnx_node.outputs()[0])
    shape = [x.dim_value if x.HasField(
        'dim_value') else -1 for x in vinfo.type.tensor_type.shape.dim]
    return OperationConverterResult(
        torch_module=TorchReshape(shape),
        onnx_mapping=OnnxMapping(
            inputs=onnx_node.inputs()[:1],
            outputs=onnx_node.outputs(),
        ),
    )
