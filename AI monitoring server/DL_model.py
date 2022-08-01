import torch.nn


class Conv1d_LSTM(nn.Module):
    def __init__(self, num_layers, hidden_unit, dropout=0.5):
        super(Conv1d_LSTM, self).__init__()
        self.hidden_unit = hidden_unit
        self.conv1d = nn.Conv1d(in_channels=6,
                                out_channels=12,
                                kernel_size=4,
                                stride=1,
                                padding=2,
                                padding_mode='replicate')
        self.avgpooling = nn.AvgPool1d(kernel_size=2, stride=1)
        self.lstm = nn.LSTM(input_size=12,
                            hidden_size=hidden_unit,
                            num_layers=num_layers,
                            bias=True,
                            dropout=dropout,
                            bidirectional=False,
                            batch_first=True)

        self.fc_layer1 = nn.Linear(self.hidden_unit, self.hidden_unit // 2)
        self.relu = nn.ReLU()
        self.fc_layer2 = nn.Linear(self.hidden_unit // 2, 1)

    def forward(self, x):
        x = x.transpose(1, 2)

        x = self.conv1d(x)
        x = self.relu(x)
        x = self.avgpooling(x)
        x = x.transpose(1, 2)

        self.lstm.flatten_parameters()
        _, (hidden, _) = self.lstm(x)
        x = hidden[-1]

        x = self.fc_layer1(x)
        x = self.relu(x)
        x = self.fc_layer2(x)

        return x