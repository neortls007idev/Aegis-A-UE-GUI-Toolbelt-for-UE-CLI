#ifndef THREADWORKER_H
#define THREADWORKER_H

#include <thread>

class ThreadWorker
{
public:
    using ThreadFunc = void (*)(void);

    explicit ThreadWorker(ThreadFunc func = nullptr);

    void Start();
    void Join();
    void Stop();
    ~ThreadWorker();

private:
    std::thread* mThread;
    ThreadFunc mFunc;
};

#endif // THREADWORKER_H
