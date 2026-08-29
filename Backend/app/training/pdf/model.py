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

class FontBranch(nn.Module):
    def __init__(self, vocab_size, pad_id, numeric_dim):
        super().__init__()
        self.pad_id = pad_id
        self.embedding = nn.Embedding(vocab_size, 32, padding_idx=pad_id)
        self.numeric = nn.Sequential(nn.Linear(numeric_dim, 32), nn.GELU())
        self.out = nn.Sequential(nn.Linear(64, 48), nn.GELU())

    def forward(self, ids, numeric):
        valid = ids.ne(self.pad_id).unsqueeze(-1)
        x = self.embedding(ids)
        pooled = (x * valid).sum(1) / valid.sum(1).clamp(min=1)
        return self.out(torch.cat([pooled, self.numeric(numeric)], 1))

class PDFDetector(nn.Module):
    def __init__(self, object_vocab_size, object_pad_id, font_vocab_size, font_pad_id, line_basic_dim, font_numeric_dim, object_numeric_dim):
        super().__init__()
        self.lexical = nn.Sequential(nn.Linear(1,16), nn.GELU(), nn.Linear(16,16), nn.GELU())
        self.objects = ObjectSequenceBranch(object_vocab_size, object_pad_id)
        self.object_numeric = nn.Sequential(nn.Linear(object_numeric_dim, 32), nn.GELU())

        self.lines = nn.Sequential(nn.Linear(line_basic_dim,48), nn.GELU(), nn.Dropout(.1), nn.Linear(48,32), nn.GELU())
        self.fonts = FontBranch(font_vocab_size, font_pad_id, font_numeric_dim)
        self.classifier = nn.Sequential(
            nn.Linear(16 + 64 + 32 + 32 + 48, 128),
            nn.GELU(),
            nn.Dropout(0.30),
            nn.Linear(128, 32),
            nn.GELU(),
            nn.Dropout(0.15),
            nn.Linear(32, 1)
        )

    def forward(self, lexical, object_ids, object_numeric, line_basic, font_ids, font_numeric):
        z = torch.cat(
            [
                self.lexical(lexical),
                self.objects(object_ids),
                self.lines(line_basic),
                self.object_numeric(object_numeric),
                self.fonts(font_ids, font_numeric)
            ], dim=1
        )

        return self.classifier(z).squeeze(1)

