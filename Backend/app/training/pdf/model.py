import torch
from torch import nn

class ObjectSequenceBranch(nn.Module):
    def __init__(self, vocab_size, pad_id, dim=64):
        super().__init__()
        self.pad_id = pad_id
        self.embedding = nn.Embedding(vocab_size, dim, padding_idx=pad_id)
        layer = nn.TransformerEncoderLayer(d_model=dim, nhead=4, dim_feedforward=256, dropout=0.15, batch_first=True, activation="gelu")
        self.encoder = nn.TransformerEncoder(layer, num_layers=2)
        self.out = nn.Sequential(nn.Linear(dim, 64), nn.GELU())

    def forward(self, ids):
        pad = ids.eq(self.pad_id)
        x = self.encoder(self.embedding(ids), src_key_padding_mask=pad)
        valid = (~pad).unsqueeze(-1)
        pooled = (x * valid).sum(1) / valid.sum(1).clamp(min=1)
        return self.out(pooled)

    