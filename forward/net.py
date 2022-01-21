import torch

# Hyper parameters
N_INPUT = 4
N_HIDDEN_LAYER = 20
N_HIDDEN = 130
N_OUTPUT = 3
ACTIVATION = torch.tanh
B_INIT = -0.2  # use a bad bias constant initializer


class Net(torch.nn.Module):
    def __init__(self):
        # 初始网络的内部结构
        super(Net, self).__init__()
        self.fcs = []
        self.bns = []
        self.bn_input = torch.nn.BatchNorm1d(N_INPUT, momentum=0.5)
        for i in range(0, N_HIDDEN_LAYER):
            input_size = N_INPUT if i == 0 else N_HIDDEN
            fc = torch.nn.Linear(input_size, N_HIDDEN)
            setattr(self, 'fc%i' % i, fc)
            self._set_init(fc)
            self.fcs.append(fc)

            bn = torch.nn.BatchNorm1d(N_HIDDEN, momentum=0.5)
            setattr(self, 'bn%i' % i, bn)
            self.bns.append(bn)

        self.predict = torch.nn.Linear(N_HIDDEN, N_OUTPUT)
        self._set_init(self.predict)

    @staticmethod
    def _set_init(layer):
        torch.nn.init.normal_(layer.weight, mean=0, std=.1)
        torch.nn.init.constant_(layer.bias, B_INIT)

    def forward(self, x):
        # 一次正向行走过程
        x = self.bn_input(x)

        for i in range(N_HIDDEN_LAYER):
            x = self.fcs[i](x)
            x = self.bns[i](x)
            x = ACTIVATION(x)
        # output
        x = self.predict(x)
        return x