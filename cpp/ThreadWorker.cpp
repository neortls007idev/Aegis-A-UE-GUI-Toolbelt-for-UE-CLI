#include "ThreadWorker.h"

ThreadWorker::ThreadWorker(ThreadFunc func)
{
    mThread = nullptr;
    mFunc = func;
}

void ThreadWorker::Start()
{
    if ( mThread == nullptr && mFunc != nullptr )
    {
        mThread = new std::thread(mFunc);
    }
}

void ThreadWorker::Join()
{
    if ( mThread != nullptr && mThread->joinable() )
    {
        mThread->join();
    }
}

void ThreadWorker::Stop()
{
    if ( mThread != nullptr )
    {
        if ( mThread->joinable() )
        {
            mThread->join();
        }
        delete mThread;
        mThread = nullptr;
    }
}

ThreadWorker::~ThreadWorker()
{
    Stop();
}
