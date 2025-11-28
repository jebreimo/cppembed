#include <iostream>
#include "data.hpp"

int main()
{
    std::cout << "Length of TXT_DATA: " << foo::TXT_DATA.size() << "\n"
              << "Length of PDF_DATA: " << foo::PDF_DATA.size() << "\n";
    std::cout << foo::ARR_DATA[0] << "\n";
    return 0;
}
