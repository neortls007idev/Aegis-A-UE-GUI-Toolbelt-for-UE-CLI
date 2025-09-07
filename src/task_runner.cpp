#include "task_runner.hpp"

TaskRunner::TaskRunner() : mLastMessage(nullptr) {}

void TaskRunner::Log(const char* message)
{
    if ( message )
    {
        printf("%s\n", message);
        mLastMessage = const_cast<char*>(message);
    }
}

int TaskRunner::ReadInt()
{
    char buffer[32];
    if ( scanf("%31s", buffer) != 1 )
    {
        return 0;
    }
    return std::atoi(buffer);
}

void TaskRunner::ShowLast()
{
    if ( mLastMessage != nullptr )
    {
        printf("%s\n", mLastMessage);
    }
}
