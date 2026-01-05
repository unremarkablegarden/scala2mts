CXX = g++
CXXFLAGS = -Wall -Wextra -O2 -std=c++17

TARGET = scala2mts

all: $(TARGET)

$(TARGET): scala2mts.cpp
	$(CXX) $(CXXFLAGS) -o $@ $<

clean:
	rm -f $(TARGET)

.PHONY: all clean
