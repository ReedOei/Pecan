import buddy


class PlotMethod:
    def plot_layer(self, k, layer, cell_bitmap):
        raise NotImplementedError()

    def show(self):
        raise NotImplementedError()

    def save(self, path):
        raise NotImplementedError()


class MatplotlibPlotMethod(PlotMethod):
    def __init__(self, color="black"):
        import matplotlib.pyplot as pt
        self.pt = pt
        self.color = color

    def show(self):
        self.pt.show()

    def save(self, path):
        self.pt.savefig(path)


"""
Plot the given cell bitmap in 1D
"""
class Matplotlib1DPlotMethod(MatplotlibPlotMethod):
    def plot_layer(self, k, layer, cell_bitmap):
        k ** layer
        for n in range(k ** layer):
            if cell_bitmap & (1 << n):
                length = 1 / k ** layer
                self.pt.plot(
                    [ n * length, n * length + length ],
                    [ layer, layer ],
                    color=self.color,
                )


"""
Plot the given cell bitmap in 2D
"""
class Matplotlib2DPlotMethod(MatplotlibPlotMethod):
    def plot_layer(self, k, layer, cell_bitmap):
        # total number of cells
        total = (k ** 2) ** layer
        length = 1 / k ** layer

        for n in range(total):
            if cell_bitmap & (1 << n):
                word = BuchiPlotter.encode_word(n, layer, k ** 2)
                x = 0
                y = 0
                for i, letter in enumerate(word):
                    x += (letter // k) * k ** (-i - 1)
                    y += (letter % k) * k ** (-i - 1)
                
                print("\r\033[2Kdrawing {}/{} squares".format(n + 1, total), end="")

                self.pt.fill(
                    [ x, x + length, x + length, x ],
                    [ y, y, y + length, y + length ],
                    self.color,
                )
        print("")


class BuchiPlotter:
    PLOT_METHOD_MAP = {
        "matplotlib": {
            1: Matplotlib1DPlotMethod(),
            2: Matplotlib2DPlotMethod(),
        },
    }

    def __init__(self, buchi_aut, dim, k, layer=None, layer_from=None, layer_to=None, save_to=None, plot_method="matplotlib"):
        super().__init__()
        self.buchi_aut = buchi_aut
        self.dim = dim
        self.k = k
        self.layer = layer
        self.layer_from = layer_from
        self.layer_to = layer_to
        self.save_to = save_to
        self.plot_method = plot_method

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
    accepted by it with the given prefix. Right now we only support
    a word on the alphabet { 0, ..., n - 1 }

    prefix should have the format "0120202", etc.
    """
    @staticmethod
    def accept_prefix(buchi_aut, prefix, n=3):
        twa = buchi_aut.aut

        # only support one argument case right now
        assert len(buchi_aut.var_map.items()) == 1, "#plot only support predicates with one free variable right now"

        # get bdd representations of each ap var
        # ap_names = buchi_aut.var_map.items[0][0]
        bdd_dict = twa.get_dict()
        bdds = [ buddy.bdd_ithvar(bdd_dict.varnum(ap_formula)) for ap_formula in twa.ap() ]

        # for bdd in bdds:
        #     print(bdd)

        # since the automata may be non-deterministic
        # keep a set of states
        current_states = { twa.state_number(twa.get_init_state()) }

        for letter in prefix:
            # assert ord(letter) >= ord("0") and ord(letter) < ord("0") + n, "illegal letter in {}".format(prefix)

            assignment_bdd = buddy.bddtrue
            # TODO: check if the most significant bit corresponds to
            # the last item in the var_map lists
            for i, bdd in enumerate(bdds):
                # test if the ith bit is 1
                if letter & (1 << (len(bdds) - i - 1)):
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
    Return a bitmap (integer) whose n^th least significant bit represents
    whether the k-ary encoding of n is a prefix of some omega-word
    """
    def get_hit_cell_bitmap(self, buchi_aut, layer):
        radix = self.k ** self.dim
        hit_bitmap = 0

        # TODO: parallelize this
        for n in range(radix ** layer):
            print("\r\033[2Kplotting layer {}: {}/{} prefixes tested".format(layer, n + 1, radix ** layer), end="")

            possibly_acc = BuchiPlotter.accept_prefix(buchi_aut, BuchiPlotter.encode_word(n, layer, radix), n=radix)
            if possibly_acc:
                hit_bitmap |= 1 << n

        # newline
        print("")

        return hit_bitmap

    def plot(self):
        if self.dim == 1:
            assert (self.layer is not None or
                    (self.layer_from is not None and self.layer_to is not None)), \
                   "one of layer or (layer_from, layer_to) must be specified"
        else:
            assert self.layer is not None, "layer must be specified for higher-dimensional plots"

        # layers is a list of tuple [(layer_num, bitmap), (layer_num, bitmap), ...]
        # that records the cell bitmap at each layer
        layers = []
        if self.dim == 1 and (self.layer_from is not None and self.layer_to is not None):
            for layer in range(self.layer_from, self.layer_to + 1):
                layers.append((layer, self.get_hit_cell_bitmap(self.buchi_aut, layer)))
        else:
            layers = [(self.layer, self.get_hit_cell_bitmap(self.buchi_aut, self.layer))]
        
        # plot all layers in the specified method
        if self.plot_method not in BuchiPlotter.PLOT_METHOD_MAP:
            raise Exception("unsupported plot method {}".format(self.plot_method))
        
        if self.dim not in BuchiPlotter.PLOT_METHOD_MAP[self.plot_method]:
            raise Exception("plot method {} cannot plot in dimension {}".format(self.plot_method, self.dim))

        plot_method = BuchiPlotter.PLOT_METHOD_MAP[self.plot_method][self.dim]
        
        for layer, cell_bitmap in layers:
            plot_method.plot_layer(self.k, layer, cell_bitmap)

        if self.save_to:
            plot_method.save(self.save_to)
        else:
            plot_method.show()
