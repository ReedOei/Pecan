#include <iostream>
#include <spot/misc/version.hh>

int main() {
  std::cout << "Hello world!\nThis is Spot " << spot::version() << ".\n";
  return 0;
}

