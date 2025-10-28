from .repository import init_db


def main():
    init_db()
    print("✅ Database initialized")


if __name__ == "__main__":
    main()


