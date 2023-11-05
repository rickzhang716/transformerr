from torch import nn
from torch import Tensor
from layers.decoder_layer import DecoderLayer
from embedding.embedding import TransformerEmbedding
from typing import Optional


class Decoder(nn.Module):
    def __init__(self,
                 num_layers: int,
                 vocab_size: int,
                 embedding_dimension: int,
                 key_dimension: int,
                 value_dimension: int,
                 max_length: int,
                 num_heads: int,
                 hidden_dimension: int,
                 epsilon: float = 1e-5,
                 dropout_probability: float = 0.1):
        super().__init__()
        self.embedding = TransformerEmbedding(vocab_size, embedding_dimension, max_length, dropout_probability)
        self.decoder_layers = nn.ModuleList([DecoderLayer(embedding_dimension,
                                                          key_dimension,
                                                          value_dimension,
                                                          num_heads,
                                                          hidden_dimension,
                                                          epsilon,
                                                          dropout_probability) for _ in range(num_layers)])

    def forward(self, x: Tensor, encoder_output: Tensor, input_mask: Tensor,
                encoder_decoder_mask: Optional[Tensor] = None):
        '''
        :param x: Tensor[batch_size, head_number, length, tensor_dimension]
        :param encoder_output: output of the final encoder layer Tensor[batch_size, head_number, length, tensor_dimension]
        :param input_mask: mask for x. We mask up to the position in the decoder, so that we do not allow for
            positions to attend to "future" positions.
        :param encoder_decoder_mask: mask for encoder_decoder attention.

        :return:
        '''
        x = self.embedding(x)
        for decoder_layer in self.decoder_layers:
            x = decoder_layer(x, encoder_output, encoder_decoder_mask, input_mask)

        return x
