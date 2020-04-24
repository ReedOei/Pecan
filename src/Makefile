PYTHON_LDFLAGS := $(shell /usr/bin/python3-config --ldflags)
PYTHON_INCLUDES := $(shell /usr/bin/python3-config --includes)
PYTHON_FLAGS := $(PYTHON_INCLUDES) $(PYTHON_LDFLAGS) -lpython3.8
all: pecan.cc
	g++ -std=c++17 pecan.cc -I$(HOME)/.local/include -L$(HOME)/.local/lib -lspot -lbddx $(PYTHON_FLAGS) -o pecan

