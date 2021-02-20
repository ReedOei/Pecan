import buddy
import spot

import numpy as np

from pecan.automata.buchi import BuchiAutomaton

from pecan.settings import settings

# A multidimensional bitmap
class Bitmap:
    # order of the dimension follows the same order as in C
    # e.g. Bitmap(2, 3) is roughly an "array": bool bitmap[2][3]
    def __init__(self, *dims):
        self.dims = dims
        self.bitmap = 0 # use pylong as the bitmap

    def get_index(self, indices):
        if type(indices) is int:
            assert indices < self.dims[0]
            return indices

        array_index = 0
        base = 1
        for dim, index in list(zip(self.dims, indices))[::-1]:
            assert index < dim, "index out of range, index {} in {}".format(indices, self.dims)
            array_index += base * index
            base *= dim

        return array_index

    def __getitem__(self, indices):
        return self.bitmap & (1 << self.get_index(indices)) != 0

    def __setitem__(self, indices, value):
        if bool(value):
            self.bitmap |= 1 << self.get_index(indices)
        else:
            self.bitmap &= ~(1 << self.get_index(indices))


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

    def cleanup(self):
        self.pt.close()

"""
Plot the given cell bitmap in 1D
"""
class Matplotlib1DPlotMethod(MatplotlibPlotMethod):
    def plot_layer(self, alphabet_sizes, layer, cell_bitmap, labels, **kwargs):
        assert len(alphabet_sizes) == 1

        base = alphabet_sizes[0] ** layer
        length = 1 / base

        for x in range(base):
            if cell_bitmap[x]:
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
    def plot_layer(self, alphabet_sizes, layer, cell_bitmap, labels, **kwargs):
        assert len(alphabet_sizes) == 2
        k1, k2 = alphabet_sizes

        # total number of cells
        total = k1 ** layer * k2 ** layer

        for x in range(k1 ** layer):
            for y in range(k2 ** layer):
                if settings.show_progress():
                    print("\r\033[2Kdrawing {}/{} squares".format(x * k2 ** layer + y + 1, total), end="")

                if cell_bitmap[x, y]:
                    self.pt.fill(
                        [ x, x + 1, x + 1, x ],
                        [ y, y, y + 1, y + 1 ],
                        self.color,
                    )
        if settings.show_progress():
            print("")

        assert len(labels) == 2
        self.pt.xlabel(labels[0])
        self.pt.ylabel(labels[1])


"""
Plot the given cell bitmap in 3D
"""
class Matplotlib3DPlotMethod(MatplotlibPlotMethod):
    def plot_layer(self, alphabet_sizes, layer, cell_bitmap, labels, color_by_axis=None, **kwargs):
        assert len(alphabet_sizes) == 3
        k1, k2, k3 = alphabet_sizes

        voxels = np.zeros((k1 ** layer, k2 ** layer, k3 ** layer), dtype=np.uint8)

        settings.log(lambda: "Preparing voxel map...")

        for x in range(k1 ** layer):
            for y in range(k2 ** layer):
                for z in range(k3 ** layer):
                    if cell_bitmap[x, y, z]:
                        voxels[x, y, z] = 1

        if color_by_axis is not None:
            settings.log(lambda: "Preparing color map...")
            colors = np.empty(np.shape(voxels), dtype=object)
            cmap = self.pt.get_cmap("jet")

            axis_index = labels.index(color_by_axis)

            for x in range(k1 ** layer):
                for y in range(k2 ** layer):
                    for z in range(k3 ** layer):
                        if axis_index == 0:
                            colors[x, y, z] = cmap(x / k1 ** layer)
                        elif axis_index == 1:
                            colors[x, y, z] = cmap(y / k2 ** layer)
                        elif axis_index == 2:
                            colors[x, y, z] = cmap(z / k3 ** layer)

        settings.log(lambda: "Drawing voxels...")

        fig = self.pt.figure()
        ax = fig.gca(projection="3d")

        if color_by_axis is not None:
            ax.voxels(voxels, facecolors=colors)
        else:
            ax.voxels(voxels)

        assert len(labels) == 3
        ax.set_xlabel(labels[0])
        ax.set_ylabel(labels[1])
        ax.set_zlabel(labels[2])

        ax.xaxis.set_ticklabels([])
        ax.yaxis.set_ticklabels([])
        ax.zaxis.set_ticklabels([])


class BuchiPlotter:
    PLOT_METHOD_MAP = {
        "matplotlib": {
            1: Matplotlib1DPlotMethod,
            2: Matplotlib2DPlotMethod,
            3: Matplotlib3DPlotMethod,
        },
    }

    def __init__(
        self,
        prog,
        alphabets,
        buchi_aut,
        layer=None,
        layer_from=None,
        layer_to=None,
        save_to='plot.png',
        show=False,
        plot_method="matplotlib",
        color_by_axis=None,
    ):
        super().__init__()
        self.prog = prog
        self.buchi_aut = buchi_aut
        self.layer = layer
        self.layer_from = layer_from
        self.layer_to = layer_to
        self.save_to = save_to
        self.alphabet_sizes = {}
        self.color_by_axis = color_by_axis # only available for 3d
        self.show = show

        self.translation_cache = {}

        self.bdds = {}
        for var, aps in buchi_aut.var_map.items():
            self.bdds[var] = [ buddy.bdd_ithvar(buchi_aut.aut.register_ap(ap)) for ap in aps ]
        self.prefix_word = spot.twa_word(buchi_aut.aut.get_dict())
        self.prefix_word.cycle.append(buddy.bddtrue)

        for k in alphabets:
            self.alphabet_sizes[k] = alphabets[k]

        # fix an arbitrary order of the arguments
        self.dimensions = list(self.alphabet_sizes.keys())

        if plot_method not in BuchiPlotter.PLOT_METHOD_MAP:
            raise Exception("unsupported plot method {}".format(plot_method))

        dim = len(self.dimensions)
        if dim not in BuchiPlotter.PLOT_METHOD_MAP[plot_method]:
            raise Exception("plot method {} cannot plot in dimension {}".format(plot_method, dim))

        self.plot_method = BuchiPlotter.PLOT_METHOD_MAP[plot_method][dim]()

    """
    Given a buchi automata, checks if there exists an omega word
    accepted by it with the given prefix.

    prefix is a word on python dictionaries, e.g.
    { "a": 1, "b": 0 } { "a": 1, "b": 2 } ...
    """
    def accept_prefix(self, prefix, n=3):
        self.prefix_word.prefix.clear()
        for dict_letter in prefix:
            assignment_bdd = buddy.bddtrue
            for var, letter in dict_letter.items():
                if (var,letter) not in self.translation_cache:
                    m = len(self.bdds[var])
                    sym = buddy.bddtrue
                    for i, bdd in enumerate(self.bdds[var]):
                        # test if the ith bit is 1
                        if letter & (1 << (m - i - 1)):
                            sym &= bdd
                        else:
                            sym &= buddy.bdd_not(bdd)
                    self.translation_cache[(var,letter)] = sym
                assignment_bdd &= self.translation_cache[(var,letter)]
            self.prefix_word.prefix.append(assignment_bdd)

        prefix_aut = self.prefix_word.as_automaton()
        accepts = self.buchi_aut.aut.intersects(prefix_aut)
        return accepts

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
        radix = 1
        for var in self.dimensions:
            radix *= self.alphabet_sizes[var]

        hit_bitmap = Bitmap(*[ self.alphabet_sizes[dim] ** layer for dim in self.dimensions ])

        # TODO: parallelize this. If we do parallelize this, remove the translation cache probably
        for n in range(radix ** layer):
            if settings.show_progress():
                print("\r\033[2Kplotting layer {}: {}/{} prefixes tested".format(layer, n + 1, radix ** layer), end="")

            word = BuchiPlotter.encode_word(n, layer, radix)
            splitted_word = []

            # split each letter into separate components
            # reject the word directly if any of the letters exceeds any of the alphabet sizes
            for letter in word:
                splitted_letter = {}
                prev_radix = 1

                for i, dim in enumerate(self.dimensions):
                    k = self.alphabet_sizes[dim]
                    component = letter // prev_radix % k
                    splitted_letter[dim] = component
                    prev_radix *= k

                splitted_word.append(splitted_letter)

            if self.accept_prefix(splitted_word):
                # each word component corresponds to one (sub)index in the bitmap
                indices = []
                for var in self.dimensions:
                    k = self.alphabet_sizes[var]
                    word_index = 0

                    for i, letter in enumerate(splitted_word):
                        word_index += k ** (len(splitted_word) - i - 1) * letter[var]

                    indices.append(word_index)

                hit_bitmap[indices] = True

        # newline
        if settings.show_progress():
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
        for layer, cell_bitmap in layers:
            self.plot_method.plot_layer(
                [ self.alphabet_sizes[dim] for dim in self.dimensions],
                layer, cell_bitmap, self.dimensions,
                color_by_axis=self.color_by_axis
            )

        if self.save_to:
            settings.log(lambda: '[INFO] Saving plot to {}'.format(self.save_to))
            self.plot_method.save(self.save_to)
            self.prog.add_generated_file(self.save_to)

        if self.show:
            self.plot_method.show()

        self.plot_method.cleanup()

