#include "main_window.hpp"
#include <cstdio>

MainWindow::MainWindow() : mRunner(nullptr) {}

void MainWindow::Show()
{
    printf("MainWindow initialized\n");
}

void MainWindow::HandleInput()
{
    char buffer[256];
    if ( scanf("%255s", buffer) == 1 )
    {
        printf("Input: %s\n", buffer);
    }
    if ( mRunner != nullptr )
    {
        mRunner->Log("Handled input");
    }
}
