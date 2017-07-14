try:
    from sshpt import main
except ImportError as e:
    from . import main


if __name__ == '__main__':
    main.main()
