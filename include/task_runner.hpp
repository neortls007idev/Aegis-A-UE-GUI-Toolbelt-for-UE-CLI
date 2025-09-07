#ifndef TASK_RUNNER_HPP
#define TASK_RUNNER_HPP

#include <cstdio>
#include <cstdlib>

class TaskRunner {
public:
    TaskRunner();
    void Log(const char* message);
    int ReadInt();
    void ShowLast();

private:
    char* mLastMessage;
};

#endif // TASK_RUNNER_HPP
