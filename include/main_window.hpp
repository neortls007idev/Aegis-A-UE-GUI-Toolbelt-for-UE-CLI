#ifndef MAIN_WINDOW_HPP
#define MAIN_WINDOW_HPP

#include "task_runner.hpp"

class MainWindow {
public:
    MainWindow();
    void Show();
    void HandleInput();

private:
    TaskRunner* mRunner;
};

#endif // MAIN_WINDOW_HPP
