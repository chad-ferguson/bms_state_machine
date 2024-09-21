from bms import BMS
from tests import run_test1, run_test2, run_test3
import time

def main():
    run_test1()
    run_test2()
    run_test3()

    print("All tests passed!")
    return 

if __name__ == "__main__":
    main()