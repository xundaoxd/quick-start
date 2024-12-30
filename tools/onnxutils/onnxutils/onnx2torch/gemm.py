import torch
from torch import nn


from onnxutils.common import OnnxModel, OnnxNode

from .registry import converter
from .utils import OnnxToTorchModule, OperationConverterResult, OnnxMapping


class TorchGemm(nn.Module, OnnxToTorchModule):
    def __init__(self, weight, bias, alpha, beta, transA, transB):
        super().__init__()
        self.alpha = alpha
        self.beta = beta
        self.transA = transA

        if transB:
            self.weight = nn.Parameter(weight.T)
        else:
            self.weight = nn.Parameter(weight)
        self.bias = nn.Parameter(bias)

    def forward(self, x):
        if self.transA:
            x = x.T
        return x @ self.weight * self.alpha + self.bias * self.beta


@converter(operation_type='Gemm', version=13)
def _(onnx_node: OnnxNode, onnx_model: OnnxModel) -> OperationConverterResult:
    alpha = onnx_node.attributes().get('alpha', 1.0)
    beta = onnx_node.attributes().get('beta', 1.0)
    transA = onnx_node.attributes().get('transA', 0)
    transB = onnx_node.attributes().get('transB', 0)

    weight = onnx_model.get_initializer_by_name(
        onnx_node.inputs()[1]).to_torch()
    bias = onnx_model.get_initializer_by_name(onnx_node.inputs()[2]).to_torch()

    return OperationConverterResult(
        torch_module=TorchGemm(weight, bias, alpha, beta, transA, transB),
        onnx_mapping=OnnxMapping(
            inputs=onnx_node.inputs()[:1],
            outputs=onnx_node.outputs(),
        ),
    )
