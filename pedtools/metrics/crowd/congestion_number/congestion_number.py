import math


class Vec2D(object):
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def __add__(self, other):
        return Vec2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Vec2D(self.x - other.x, self.y - other.y)

    def __mul__(self, val):
        return Vec2D(self.x * val, self.y * val)

    def __truediv__(self, val):
        assert (val > 0)
        new_val = 1 / val
        return self.__mul__(new_val)

    def __str__(self):
        return f'{self.x:.5f} {self.y:.5f}'


class VelCell:
    def __init__(self):
        self.v = Vec2D()
        self.dens = 0
        self.rotval = False
        self.rot = 0
        self.cn = 0
        self.update_count = 0

    def add(self, new_v):
        self.v += new_v
        self.dens += 1


class Grid:
    def __init__(self, CellType, x_size=5, y_size=5, delta_x=1, delta_y=1, x_min=0, y_min=0):
        self.cell_list = []  # empty list to hold all cells
        self.delta_x = float(delta_x)
        self.delta_y = float(delta_y)
        self.x_min = float(x_min)
        self.y_min = float(y_min)
        self.x_size = int(x_size)
        self.y_size = int(y_size)
        for col in range(self.x_size):
            col_list = []
            for row in range(self.y_size):
                cell = CellType()
                col_list.append(cell)
            self.cell_list.append(col_list)

    def __getitem__(self, index):
        return self.cell_list[index]

    def valid_idx(self, x_idx, y_idx):
        valid = True
        if (x_idx >= len(self.cell_list)) or x_idx < 0:
            valid = False
        if (y_idx >= len(self.cell_list[x_idx])) or y_idx < 0:
            valid = False
        return valid

    def write_to_file_v(self, fname):
        with open(fname, 'w') as fp:
            for cell_coll in self.cell_list:
                for cell in cell_coll:
                    fp.write(f"{cell.v} ")
                fp.write('\n')

    def write_to_file(self, fname, attribute='rot'):
        with open(fname, 'w') as fp:
            for cell_coll in self.cell_list:
                for cell in cell_coll:
                    fp.write(f"{cell.__dict__[attribute]:.5f} ")
                fp.write('\n')


class BoolGrid(Grid):
    def __init__(self, x_size=5, y_size=5, delta_x=1, delta_y=1, x_min=0, y_min=0):
        super().__init__(bool, x_size, y_size, delta_x, delta_y, x_min, y_min)


class VelocityGrid(Grid):
    def __init__(self, rep_id, x_size=5, y_size=5, delta_x=1, delta_y=1, x_min=0, y_min=0):
        self.rep_id = int(rep_id)
        # self.update_count=0
        super().__init__(VelCell, x_size, y_size, delta_x, delta_y, x_min, y_min)

    def update_velocity_field(self, ped_state):

        x_idx = int((ped_state['x'] - self.x_min) / self.delta_x)
        y_idx = int((ped_state['y'] - self.y_min) / self.delta_y)
        if self.valid_idx(x_idx, y_idx):
            # self.update_count+=1
            self.cell_list[x_idx][y_idx].add(ped_state['v'])
        else:
            print(f" Ignoring pedestrian at x: {ped_state['x']},y: {ped_state['y']}, rep: {self.rep_id}")

    def scale_velocity_field(self, in_area):
        for i in range(self.x_size):
            for j in range(self.y_size):
                cell = self.cell_list[i][j]
                if cell.dens > 0:
                    cell.v /= cell.dens
                    # print(cell.dens,cell.update_count)
                    cell.dens /= cell.update_count * (self.delta_x * self.delta_y)
                    if cell.dens > 0:
                        in_area[i][j] = True

    def check_neighs(self, i, j):  # checks if velocity field defined in neighs
        grid = self.cell_list
        if ((grid[i - 1][j].dens > 0) and (grid[i + 1][j].dens > 0) and (grid[i][j - 1].dens > 0) and (
                grid[i][j + 1].dens > 0)):
            return True
        return False

    def calc_rotor(self):
        grid = self.cell_list
        for i in range(1, self.x_size - 1):
            for j in range(1, self.y_size - 1):
                if self.check_neighs(i, j):
                    grid[i][j].rotval = True
                    grid[i][j].rot = (grid[i + 1][j].v.y - grid[i - 1][j].v.y - grid[i][j + 1].v.x + grid[i][
                        j - 1].v.x) / (2 * self.delta_x)  # CHECK

    def calc_cn(self, cn_radius):
        d_cnr = int(cn_radius) + 1  # r=3.5-> d_cnr=4 for loop on neighs
        grid = self.cell_list
        for i in range(self.x_size):
            for j in range(self.y_size):
                conta_v = 0  # number of non zero vel cells
                vav = 0  # average vel in ROI
                maxr = float('-inf')  # max,min of rot
                minr = float('inf')  #
                for l in range(-d_cnr, d_cnr):
                    for m in range(-d_cnr, d_cnr):  # scans over neighs
                        r = math.sqrt(l * l + m * m)  # euclidean condition
                        if (((i + l) >= 0) and ((j + m) >= 0) and ((i + l) < self.x_size) and (
                                (j + m) < self.y_size) and (r <= cn_radius)):
                            if grid[i + l][j + m].rotval:  # if rot defined looks for max and min
                                if grid[i + l][j + m].rot > maxr:
                                    maxr = grid[i + l][j + m].rot
                                if grid[i + l][j + m].rot < minr:
                                    minr = grid[i + l][j + m].rot
                            if grid[i + l][j + m].v.magnitude() > 0:  # if vel defined updates average
                                conta_v += 1
                                vav += grid[i + l][j + m].v.magnitude()
                if (conta_v):  # computes average and cn
                    vav /= conta_v;
                    if (maxr != float('-inf')) and (minr != float('inf')):
                        grid[i][j].cn = self.delta_x * (maxr - minr) / (
                                vav * 6)  # Needs to be updated for different dx dy
                    else:
                        grid[i][j].cn = 0  # zero if v nowhere or rot nowhere
                else:
                    grid[i][j].cn = 0


class GridCollection:
    def __init__(self, num_repetitions, num_timesteps, x_size, y_size, delta_x, delta_y, x_min, y_min, delta_t):
        self.grid_collection = []
        self.in_area = BoolGrid(x_size, y_size, delta_x, delta_y, x_min, y_min)
        self.delta_t = delta_t
        self.num_repetitions = num_repetitions
        self.num_timesteps = num_timesteps
        for rep in range(num_repetitions):
            rep_grids = []
            for tstep in range(num_timesteps):
                g = VelocityGrid(rep, x_size, y_size, delta_x, delta_y, x_min, y_min)
                rep_grids.append(g)
            self.grid_collection.append(rep_grids)

    def valid_idx(self, rep_idx, t_idx):
        valid = True
        if rep_idx < 0 or rep_idx >= len(self.grid_collection):
            valid = False
        if t_idx < 0 or t_idx >= len(self.grid_collection[rep_idx]):
            valid = False
        return valid

    def update(self, sim, time, ped_state):
        rep_idx = int(sim)
        t_idx = int(time / self.delta_t)
        if self.valid_idx(rep_idx, t_idx):
            self.grid_collection[rep_idx][t_idx].update_velocity_field(ped_state)
        else:
            print(f" Ignoring pedestrian from rep:{sim}, time:{time}")

    def write_velocity(self):
        for rep_idx in range(self.num_repetitions):
            for t_idx in range(self.num_timesteps):
                fname = f'data/TEST_R_{rep_idx}_T_{t_idx}'
                grid = self.grid_collection[rep_idx][t_idx]
                grid.write_to_file_v(fname)

    def write_rotor(self):
        for rep_idx in range(self.num_repetitions):
            for t_idx in range(self.num_timesteps):
                fname = f'data/TEST_R_{rep_idx}_T_{t_idx}'
                grid = self.grid_collection[rep_idx][t_idx]
                grid.write_to_file(fname, attribute="rot")

    def write_cn(self):
        for rep_idx in range(self.num_repetitions):
            for t_idx in range(self.num_timesteps):
                fname = f'data/TEST_R_{rep_idx}_T_{t_idx}'
                grid = self.grid_collection[rep_idx][t_idx]
                grid.write_to_file(fname, attribute="cn")

    def calc_rotor(self):
        for rep_idx in range(self.num_repetitions):
            for t_idx in range(self.num_timesteps):
                grid = self.grid_collection[rep_idx][t_idx]
                grid.calc_rotor()

    def scale_velocity_field(self):
        for rep_idx in range(self.num_repetitions):
            for t_idx in range(self.num_timesteps):
                grid = self.grid_collection[rep_idx][t_idx]
                grid.scale_velocity_field(self.in_area)

    def calc_cn(self, cn_radius):
        for rep_idx in range(self.num_repetitions):
            for t_idx in range(self.num_timesteps):
                grid = self.grid_collection[rep_idx][t_idx]
                grid.calc_cn(cn_radius)

    # TODO
    def up_all(self, rep_idx, time):
        t_idx = int(time / self.delta_t)
        if t_idx < self.num_timesteps:
            grid = self.grid_collection[rep_idx][t_idx]
            for i in range(grid.x_size):
                for j in range(grid.y_size):
                    grid[i][j].update_count += 1

    def init_velocity_field(self):
        for rep_idx in range(self.num_repetitions):
            fname = f'positions/pos_{rep_idx}.dat'
            with open(fname) as fp:
                line = fp.readline()
                while line:
                    time, ped_count = line.strip().split(' ')
                    time = float(time)
                    self.up_all(rep_idx, time)
                    ped_count = int(ped_count)
                    line = fp.readline().strip().split(' ')
                    if ped_count:
                        for i in range(ped_count):
                            idx = i * 4
                            x = float(line[idx])
                            y = float(line[idx + 1])
                            vx = float(line[idx + 2])
                            vy = float(line[idx + 3])
                            ped_state = {
                                'x': x,
                                'y': y,
                                'v': Vec2D(vx, vy)
                            }
                            self.update(rep_idx, time, ped_state)
                    line = fp.readline()


class Params:
    def __init__(self):
        self.params = {}
        self.read()

    def read(self, fname='parameters'):
        with open(fname) as fp:
            line = fp.readline()
            while line:
                key, val = line.strip().split(' ')
                self.params[key] = float(val)
                line = fp.readline()


class StatsCell:  # for statistics
    def __init__(self):
        self.conta = 0  # counter
        self.av = 0  # average
        self.sg = 0  # standard dev
        self.er = 0  # std err

    def update(self, up):
        self.av += up
        self.sg += up * up
        self.conta += 1

    def finalize(self):  # computes everything
        if (self.conta):
            self.av /= self.conta
            self.sg /= self.conta

        if (self.conta > 1):
            self.sg = math.sqrt(self.sg - self.av ** 2)
            self.er = self.sg / math.sqrt(self.conta - 1)
        else:
            self.sg = 0
            self.er = 0


class DDistr:  # includes a vector and a matrix for statistics
    def __init__(self, r, num_timesteps, dt):  # intialises giving # of reps, maximum time and time step
        self.repetition = r
        self.delta_t = dt
        self.delta_t_2 = self.delta_t * 0.5
        self.time_steps = num_timesteps
        self.d = [StatsCell() for i in range(self.time_steps)]
        self.dd = []
        self.imr = 0
        self.imt = 0
        for i in range(self.repetition):
            self.dd.append([StatsCell() for j in range(self.time_steps)])
        self.max_val = -1e10  # very negative max initialisation

    def update(self, up, r, t):  # adds up to the statistics
        it = int(t / self.delta_t)
        self.dd[r][it].update(up)

    def finalize(self):  # finalises
        for t in range(self.time_steps):
            for r in range(self.repetition):
                if self.dd[r][t].av > self.max_val:  # //finds max
                    self.max_val = self.dd[r][t].av
                    self.imr = r
                    self.imt = t
                self.d[t].update(self.dd[r][t].av)  # puts in vector the average over reps
            self.d[t].finalize()  # stats over reps, now in d we have av,sg, and er over reps depending on time

    def write_to_file(self, fname):
        with open(fname, 'w') as fp:
            for i in range(self.time_steps):
                ostring = f"{i * self.delta_t + self.delta_t_2:.5f} {self.d[i].av - self.d[i].er:.5f} {self.d[i].av:.5f} {self.d[i].av + self.d[i].er:.5f}\n"
                fp.write(ostring)


class Statistics:
    def __init__(self, gc):
        self.gc = gc
        self.av_cn = DDistr(gc.num_repetitions, gc.num_timesteps, gc.delta_t)
        self.max_cn = DDistr(gc.num_repetitions, gc.num_timesteps, gc.delta_t)
        self.av_in_cn = DDistr(gc.num_repetitions, gc.num_timesteps, gc.delta_t)
        self.dens = DDistr(gc.num_repetitions, gc.num_timesteps, gc.delta_t)

    def calc_statistics(self):
        for rep_idx in range(self.gc.num_repetitions):
            for t_idx in range(self.gc.num_timesteps):
                loc_max = 0
                grid = self.gc.grid_collection[rep_idx][t_idx]
                for i in range(grid.x_size):
                    for j in range(grid.y_size):
                        if grid[i][j].cn > 0:
                            self.av_cn.dd[rep_idx][t_idx].update(grid[i][j].cn)
                            if grid[i][j].cn > loc_max:
                                loc_max = grid[i][j].cn
                        if self.gc.in_area[i][j]:
                            self.dens.dd[rep_idx][t_idx].update(grid[i][j].dens)
                            self.av_in_cn.dd[rep_idx][t_idx].update(grid[i][j].cn)
                self.dens.dd[rep_idx][t_idx].finalize()
                self.av_cn.dd[rep_idx][t_idx].finalize()
                self.max_cn.dd[rep_idx][t_idx].av = loc_max
                self.av_in_cn.dd[rep_idx][t_idx].finalize()
        self.dens.finalize()
        self.max_cn.finalize()
        self.av_cn.finalize()
        self.av_in_cn.finalize()