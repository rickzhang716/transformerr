
import torch
from torch.optim.lr_scheduler import LambdaLR
from training.utils import LabelSmoothing, rate, no_peek_mask
from training.train import run_epoch
from .data import data_gen
from .dummy import DummyOptimizer, DummyScheduler, Generator
from model.transformer import Transformer


def example_simple_model():
    vocab_size = 11
    criterion = LabelSmoothing(size=vocab_size, padding_idx=0, smoothing=0.0)
    model = Transformer(vocab_size, vocab_size, num_layers=2)

    optimizer = torch.optim.Adam(
        model.parameters(), lr=0.5, betas=(0.9, 0.98), eps=1e-9
    )
    lr_scheduler = LambdaLR(
        optimizer=optimizer,
        lr_lambda=lambda step: rate(
            step, model_size=model.embedding_dimension, factor=1.0, warmup=400
        ),
    )
    generator = Generator(model.embedding_dimension, vocab_size)
    batch_size = 80
    for epoch in range(20):
        model.train()
        run_epoch(
            data_gen(vocab_size, batch_size, 20),
            model,
            SimpleLossCompute(generator, criterion),
            optimizer,
            lr_scheduler,
            mode="train",
        )
        model.eval()
        run_epoch(
            data_gen(vocab_size, batch_size, 5),
            model,
            SimpleLossCompute(generator, criterion),
            DummyOptimizer(),
            DummyScheduler(),
            mode="eval",
        )[0]

    model.eval()
    src = torch.LongTensor([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]])
    max_len = src.shape[1]
    src_mask = torch.ones(1, 1, max_len)
    print(greedy_decode(model, src, src_mask, max_len=max_len, start_symbol=0))


class SimpleLossCompute:
    #  A simple loss compute and train function.

    def __init__(self, generator, criterion):
        self.generator = generator
        self.criterion = criterion

    def __call__(self, x, y, norm):
        x = self.generator(x)
        sloss = (
            self.criterion(
                x.contiguous().view(-1, x.size(-1)), y.contiguous().view(-1)
            )
            / norm
        )
        return sloss.data * norm, sloss


def greedy_decode(model, src, src_mask, max_len, start_symbol):
    memory = model.encode(src, src_mask)
    ys = torch.zeros(1, 1).fill_(start_symbol).type_as(src.data)
    for i in range(max_len - 1):
        out = model.decode(
            memory, src_mask, ys, no_peek_mask(ys.size(1)).type_as(src.data)
        )
        prob = model.generator(out[:, -1])
        _, next_word = torch.max(prob, dim=1)
        next_word = next_word.data[0]
        ys = torch.cat(
            [ys, torch.zeros(1, 1).type_as(src.data).fill_(next_word)], dim=1
        )
    return ys
