
import torch
import math
import numpy as np
import torch.nn.functional as F
from forward.net import Net
from forward.dataset import DataSet
device = torch.device("cpu")


POP_SIZE = DataSet().vx_matrix.shape[0]                  # population size
CROSS_RATE = 0.4                                         # mating probability (DNA crossover)
MUTATION_RATE = 0.05                                     # mutation probability
N_GENERATIONS = 1000
DNA_SIZE = DataSet().vx_matrix.shape[1]
I_BOUND = [29, 45]                                       # 电流取值范围
SPEED_BOUND = [700, 2301]                                # 打标速度取值范围
Q_F_BOUND = [10, 23]                                     # Q频取值范围
Q_S_BOUND = [5, 46]                                      # Q释放取值范围
LAB = torch.Tensor([81.09, 0.72, -3.37])                                 # 目标LAB值
# 29	2300	10	35

class GA(object):
    def __init__(self, DNA_size, DNA_bound_I, DNA_bound_speed, DNA_bound_qf, DNA_bound_qs, cross_rate, mutation_rate, pop_size, LAB):
        self.DNA_size = DNA_size
        self.DNA_bound_I = DNA_bound_I
        self.DNA_bound_speed = DNA_bound_speed
        self.DNA_bound_qf = DNA_bound_qf
        self.DNA_bound_qs = DNA_bound_qs
        self.cross_rate = cross_rate
        self.mutate_rate = mutation_rate
        self.pop_size = pop_size
        self.LAB = LAB
        self.pop = DataSet().vx_matrix

    def F(self, x):
        model = Net()
        model.load_state_dict(torch.load('../forward/model.pl', map_location=device))
        model.eval()
        lab = model(x)
        return lab

    def get_fitness(self, preds):                      # count how many character matches
        match_count = []
        for pred in preds:
             match_count.append(1/F.mse_loss(pred, self.LAB).item())
        return match_count

    def select(self):
        fitness = self.get_fitness(self.F(self.pop))     # add a small amount to avoid all zero fitness
        fitness = np.array(fitness)
        idx = np.random.choice(np.arange(self.pop_size), size=self.pop_size, replace=True, p=fitness/fitness.sum())
        return self.pop[idx]

    def crossover(self, parent, pop):
        if np.random.rand() < self.cross_rate:
            i_ = np.random.randint(0, self.pop_size, size=1)                        # select another individual from pop
            cross_points = np.random.randint(0, 2, self.DNA_size).astype(np.bool)   # choose crossover points
            parent[cross_points] = pop[i_, cross_points]                            # mating and produce one child
        return parent

    def mutate(self, child):
        for point in range(self.DNA_size):
            if np.random.rand() < self.mutate_rate:
                if point == 0:
                    child[point] = np.random.randint(*self.DNA_bound_I)
                elif point == 1:
                    child[point] = np.random.randint(*self.DNA_bound_speed)
                elif point == 2:
                    child[point] = np.random.randint(*self.DNA_bound_qf)
                else:
                    child[point] = np.random.randint(*self.DNA_bound_qs)
        return child

    def evolve(self):
        pop = self.select()
        pop_copy = pop
        for parent in pop:  # for every parent
            child = self.crossover(parent, pop_copy)
            child = self.mutate(child)
            parent[:] = child
        self.pop = pop


if __name__ == '__main__':
    ga = GA(DNA_size=DNA_SIZE, DNA_bound_I=I_BOUND, DNA_bound_speed=SPEED_BOUND,
            DNA_bound_qf=Q_F_BOUND, DNA_bound_qs=Q_S_BOUND, cross_rate=CROSS_RATE,
            mutation_rate=MUTATION_RATE, pop_size=POP_SIZE, LAB=LAB)

    count = 0
    res = 0
    for generation in range(N_GENERATIONS):
        fitness = ga.get_fitness(ga.F(ga.pop))
        best_DNA = ga.pop[np.argmax(fitness)].unsqueeze(0)
        loss_func = F.mse_loss
        predictions = ga.F(best_DNA)
        train_loss = loss_func(predictions, ga.LAB).to(device)
        print('Gen', generation, ': ', best_DNA, ' loss:' , train_loss.item())

        if res == 0 or res == train_loss.item():
            count += 1
        else:
            count = 0
        res = train_loss.item()
        if count == 20:                  # 重复20次中断循环
            print("find the result :", best_DNA, "with LAB: ", ga.F(best_DNA))
            break

        ga.evolve()