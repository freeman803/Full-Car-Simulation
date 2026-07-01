import numpy as np
import pandas as pd
import scipy


def main() -> None:
    print("Full-Car-Simulation environment OK")
    print(f"  numpy  {np.__version__}")
    print(f"  scipy  {scipy.__version__}")
    print(f"  pandas {pd.__version__}")


if __name__ == "__main__":
    main()
