import sys

from examples import example_basic
from examples import example_buffers
from examples import example_shifts
from examples import example_multiobjective

def main():
    """
    Fő belépési pont a szimulátorhoz. Menüből kiválasztható a futtatni kívánt példa.
    """
    print("=" * 60)
    print(" Job Shop Folyamatszimulátor - GEIAK140-B")
    print(" Készítette: Hallgató (Miskolci Egyetem, 2026)")
    print("=" * 60)
    
    while True:
        print("\nVálasszon a futtatni kívánt mintapéldák közül:")
        print("1. Elégséges szint: Alap szimuláció (FIFO vs SPT, végtelen puffer)")
        print("2. Közepes szint: Korlátozott puffer és blokkolás bemutatása")
        print("3. Jó szint: Gép rendelkezésre állás (Műszakok)")
        print("4. Jeles szint: Többcélú ütemezés és Prediktív kereső (Hill Climbing)")
        print("0. Kilépés")
        
        choice = input("\nAdja meg a menüpont számát: ")
        
        if choice == '1':
            example_basic.run()
        elif choice == '2':
            example_buffers.run()
        elif choice == '3':
            example_shifts.run()
        elif choice == '4':
            example_multiobjective.run()
        elif choice == '0':
            print("Kilépés...")
            sys.exit(0)
        else:
            print("Érvénytelen választás, kérem próbálja újra.")

if __name__ == "__main__":
    main()
