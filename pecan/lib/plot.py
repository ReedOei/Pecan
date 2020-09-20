import buddy
import spot

import numpy as np


class PlotMethod:
    def plot_layer(self, k, layer, cell_bitmap, labels):
        raise NotImplementedError()

    def show(self):
        raise NotImplementedError()

    def save(self, path):
        raise NotImplementedError()


class MatplotlibPlotMethod(PlotMethod):
    def __init__(self, color="blue"):
        import matplotlib.pyplot as pt
        self.pt = pt
        self.color = color

    def show(self):
        self.pt.tight_layout()
        self.pt.show()

    def save(self, path):
        self.pt.tight_layout()
        self.pt.savefig(path)


"""
Plot the given cell bitmap in 1D
"""
class Matplotlib1DPlotMethod(MatplotlibPlotMethod):
    def plot_layer(self, k, layer, cell_bitmap, labels):
        base = k ** layer
        length = 1 / base

        for x in range(base):
            if cell_bitmap & (1 << x):
                self.pt.plot(
                    [ x * length, x * length + length ],
                    [ layer, layer ],
                    color=self.color,
                )

        assert len(labels) == 1
        self.pt.xlabel(labels[0])
        self.pt.ylabel("layer")


"""
Plot the given cell bitmap in 2D
"""
class Matplotlib2DPlotMethod(MatplotlibPlotMethod):
    def plot_layer(self, k, layer, cell_bitmap, labels):
        # total number of cells
        base = k ** layer
        total = (k ** layer) ** 2

        for x in range(k ** layer):
            for y in range(k ** layer):
                array_index = x * base + y
                print("\r\033[2Kdrawing {}/{} squares".format(array_index + 1, total), end="")

                if cell_bitmap & (1 << array_index):
                    self.pt.fill(
                        [ x, x + 1, x + 1, x ],
                        [ y, y, y + 1, y + 1 ],
                        self.color,
                    )
        print("")

        assert len(labels) == 2
        self.pt.xlabel(labels[0])
        self.pt.ylabel(labels[1])


"""
Plot the given cell bitmap in 3D
"""
class Matplotlib3DPlotMethod(MatplotlibPlotMethod):
    def plot_layer(self, k, layer, cell_bitmap, labels):
        voxels = np.zeros((k ** layer, k ** layer, k ** layer), dtype=np.uint8)
        base = k ** layer

        print("preparing voxel map")

        for x in range(base):
            for y in range(base):
                for z in range(base):
                    array_index = x * base * base + y * base + z
                    if cell_bitmap & (1 << array_index):
                        voxels[x, y, z] = 1

        print("drawing voxels")

        fig = self.pt.figure()
        ax = fig.gca(projection="3d")
        ax.voxels(voxels)

        assert len(labels) == 3
        ax.set_xlabel(labels[0])
        ax.set_ylabel(labels[1])
        ax.set_zlabel(labels[2])


class BuchiPlotter:
    PLOT_METHOD_MAP = {
        "matplotlib": {
            1: Matplotlib1DPlotMethod(),
            2: Matplotlib2DPlotMethod(),
            3: Matplotlib3DPlotMethod(),
        },
    }

    def __init__(self, buchi_aut, layer=None, layer_from=None, layer_to=None, save_to=None, plot_method="matplotlib", **kwargs):
        super().__init__()
        self.buchi_aut = buchi_aut
        self.layer = layer
        self.layer_from = layer_from
        self.layer_to = layer_to
        self.save_to = save_to
        self.plot_method = plot_method
        self.alphabet_sizes = {}
        self.max_alphabet_size = 0

        for key in kwargs:
            if key.startswith("alphabet_"):
                self.alphabet_sizes[key[len("alphabet_"):]] = kwargs[key]
                self.max_alphabet_size = max(self.max_alphabet_size, kwargs[key])

        # fix an arbitrary order of the arguments
        self.dimensions = list(self.alphabet_sizes.keys())

        assert self.max_alphabet_size > 0

    # find the reachable states from the given initial states
    @staticmethod
    def find_reachable(buchi_aut, states):
        reachable = set(states)
        queue = list(states)
        while len(queue):
            state = queue.pop()
            for edge in buchi_aut.aut.out(state):
                # only follow satisfiable edges
                if edge.cond != buddy.bddfalse:
                    if edge.dst not in reachable:
                        reachable.add(edge.dst)
                        queue = [edge.dst] + queue
        return reachable

    """
    Given a buchi automata, checks if there exists an omega word
    accepted by it with the given prefix.

    prefix is a word on python dictionaries, e.g.
    { "a": 1, "b": 0 } { "a": 1, "b": 2 } ...
    """
    @staticmethod
    def accept_prefix(buchi_aut, prefix, n=3):
        twa = buchi_aut.aut

        # only support one argument case right now
        # assert len(buchi_aut.var_map.items()) == 1, "#plot only support predicates with one free variable right now"

        # get bdd representations of each ap var
        bdd_dict = twa.get_dict()

        bdds = {}
        for var, aps in buchi_aut.var_map.items():
            bdds[var] = [ buddy.bdd_ithvar(bdd_dict.varnum(spot.formula(ap))) for ap in aps ]

        # check if the variables match
        if len(prefix):
            first_letter = prefix[0]
            word_variables = set(first_letter.keys())
            bdd_variables = set(bdds.keys())
            assert word_variables == bdd_variables, \
                   "unmatched number of dimenstions, expecting {}, got {}".format(bdd_variables, word_variables)

        # since the automata may be non-deterministic
        # keep a set of states
        current_states = { twa.state_number(twa.get_init_state()) }
        for dict_letter in prefix:
            # NOTE: letter is a dictionary from variable => actual letters
            assignment_bdd = buddy.bddtrue
            # TODO: check if the most significant bit corresponds to
            # the last item in the var_map lists
            for var, letter in dict_letter.items():
                for i, bdd in enumerate(bdds[var]):
                    # test if the ith bit is 1
                    if letter & (1 << (len(bdds[var]) - i - 1)):
                        assignment_bdd = buddy.bdd_and(assignment_bdd, bdd)
                    else:
                        assignment_bdd = buddy.bdd_and(assignment_bdd, buddy.bdd_not(bdd))

            # check all outgoing edges and update the current state set
            next_states = set()

            for state in current_states:
                for edge in twa.out(state):
                    # print(buddy.bdd_printset(edge.cond))
                    satisfiable = buddy.bdd_and(edge.cond, assignment_bdd) != buddy.bddfalse
                    # print(edge.cond, assignment_bdd, buddy.bdd_and(edge.cond, assignment_bdd))
                    if satisfiable:
                        next_states.add(edge.dst)

            # print(current_states, letter, next_states)

            current_states = next_states

        # TODO: we are assuming that all states are accepting
        # states (non-accepting ones should be removed from the
        # automata already)
        return len(current_states) != 0

        # # find all reachable states T1
        # # find all states reachable by T, T2
        # # take T = T1 /\ T2, which is the set of states
        # # that can be visited infinitely many times
        # t1 = self.find_reachable(buchi_aut, current_states)
        # t2 = self.find_reachable(buchi_aut, t1)
        # inf_set = t1.intersection(t2)

        # # checks if there is a satisfiable path from the current state to an accepting state
        # # twa.get_acceptance().used_sets()

        # # https://spot.lrde.epita.fr/doxygen/structspot_1_1acc__cond_1_1acc__code.html
        # # assuming acc_cond is of the form `Inf(i)`
        # acc_cond = twa.get_acceptance()
        # print(dir(acc_cond))
        # # print(spot.acc_cond.all_sets(acc_cond))
        # print(twa.get_acceptance())
        # print(current_states)

    @staticmethod
    def encode_word(n, layer, radix):
        s = [ (n // (radix ** i)) % radix for i in range(layer) ]
        s.reverse()
        return s

    """
    Return a bitmap (integer) which can be bitwisely interpreted
    as a voxel map of dimension (<k> ** <layer>) x (<k> ** <layer>) x ... x (<k> ** <layer>)
                                |______________________<dim> mults_________________________|
    where k is the maximum alphabet size, dim is the number of variables in the buchi automata var_map
    
    In the bitmap, each true bit means the corresponding cell contains an omega word that
    is accepted by <buchi_aut>
    """
    def get_hit_cell_bitmap(self, buchi_aut, layer):
        # sample using the highest largest alphabet size first
        radix = self.max_alphabet_size ** len(self.dimensions)
        hit_bitmap = 0

        # TODO: parallelize this
        for n in range(radix ** layer):
            print("\r\033[2Kplotting layer {}: {}/{} prefixes tested".format(layer, n + 1, radix ** layer), end="")

            word = BuchiPlotter.encode_word(n, layer, radix)
            splitted_word = []
            early_reject = False

            # split each letter into separate components
            # reject the word directly if any of the letters exceeds any of the alphabet sizes
            for letter in word:
                splitted_letter = {}

                for i, dim in enumerate(self.dimensions):
                    component = letter // (self.max_alphabet_size ** i) % self.max_alphabet_size
                    if component > self.alphabet_sizes[dim]:
                        early_reject = True
                        break
                    splitted_letter[dim] = component

                if early_reject: break
                splitted_word.append(splitted_letter)

            possibly_acc = not early_reject and BuchiPlotter.accept_prefix(buchi_aut, splitted_word)

            if possibly_acc:
                # convert n to actual coordinates
                k = self.max_alphabet_size
                dim = len(self.dimensions)
                base = k ** layer

                # <dim> coordinates encoded into one array index, e.g.
                # x, y, z => x * base ** 2 + y * base + z
                array_index = 0
                for i, letter in enumerate(splitted_word):
                    for j, var in enumerate(self.dimensions):
                        array_index += base ** (dim - j - 1) * (k ** (len(splitted_word) - i - 1)) * letter[var]

                hit_bitmap |= 1 << array_index

        # newline
        print("")

        return hit_bitmap

    def plot(self):
        dim = len(self.dimensions)

        if dim == 1:
            assert (self.layer is not None or
                    (self.layer_from is not None and self.layer_to is not None)), \
                   "one of layer or (layer_from, layer_to) must be specified"
        else:
            assert self.layer is not None, "layer must be specified for higher-dimensional plots"

        # layers is a list of tuple [(layer_num, bitmap), (layer_num, bitmap), ...]
        # that records the cell bitmap at each layer
        layers = []
        if dim == 1 and (self.layer_from is not None and self.layer_to is not None):
            for layer in range(self.layer_from, self.layer_to + 1):
                layers.append((layer, self.get_hit_cell_bitmap(self.buchi_aut, layer)))
        else:
            layers = [(self.layer, self.get_hit_cell_bitmap(self.buchi_aut, self.layer))]
        
        # plot all layers in the specified method
        if self.plot_method not in BuchiPlotter.PLOT_METHOD_MAP:
            raise Exception("unsupported plot method {}".format(self.plot_method))
        
        if dim not in BuchiPlotter.PLOT_METHOD_MAP[self.plot_method]:
            raise Exception("plot method {} cannot plot in dimension {}".format(self.plot_method, dim))

        plot_method = BuchiPlotter.PLOT_METHOD_MAP[self.plot_method][dim]
        
        for layer, cell_bitmap in layers:
            plot_method.plot_layer(self.max_alphabet_size, layer, cell_bitmap, self.dimensions)

        if self.save_to:
            plot_method.save(self.save_to)
        else:
            plot_method.show()
