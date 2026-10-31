"""Jalankan worker hello: ``python -m hello_worker``."""

from lab_worker.worker import run_forever

from hello_worker.handlers import HANDLERS


def main() -> None:
    run_forever(HANDLERS)


if __name__ == "__main__":
    main()
