import subprocess
from pathlib import Path


def test_ThreadWorker(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cpp_dir = repo_root / "cpp"

    main_src = tmp_path / "main.cpp"
    main_src.write_text(
        """#include <iostream>
#include \"ThreadWorker.h\"

void Run()
{
    std::cout << \"thread ran\" << std::endl;
}

int main()
{
    ThreadWorker worker(Run);
    worker.Start();
    worker.Join();
    worker.Stop();
    return 0;
}
"""
    )

    executable = tmp_path / "test_ThreadWorker"
    subprocess.run(
        [
            "g++",
            "-std=c++17",
            str(cpp_dir / "ThreadWorker.cpp"),
            str(main_src),
            "-I",
            str(cpp_dir),
            "-pthread",
            "-o",
            str(executable),
        ],
        check=True,
    )
    result = subprocess.run(
        [str(executable)], capture_output=True, text=True, check=True
    )
    assert "thread ran" in result.stdout
