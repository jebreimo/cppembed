#include <iostream>
#include "pdf_data.hpp"
#include "txt_data.hpp"

int main()
{
    std::cout << "Length of TXT_DATA: " << foo::TXT_DATA.size() << "\n"
              << "Length of PDF_DATA: " << foo::PDF_DATA.size() << "\n";
    return 0;
}
