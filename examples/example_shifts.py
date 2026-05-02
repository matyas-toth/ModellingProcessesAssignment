import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Job, Operation, Machine
from simulator import Simulator
from scheduler import fifo_rule
from evaluator import Evaluator
from visualizer import Visualizer

def get_shifts_data():
    """
    3. példa – Jó szint:
    4 munka, 3 gép. Gép rendelkezésre állás (műszakok) beállítása.
    M1 és M3 csak műszakban megy (0-480, majd 960-1440).
    M2 folyamatosan (0-2000).
    Az időegységek itt perceket jelentenek.
    """
    machines = {
        "M1": Machine("M1", availability_windows=[(0, 480), (960, 1440), (1920, 2400)]),
        "M2": Machine("M2", availability_windows=[(0, 3000)]), # Gyakorlatilag folyamatos
        "M3": Machine("M3", availability_windows=[(0, 480), (960, 1440), (1920, 2400)])
    }

    # Hosszú műveletekkel, hogy átlógjanak a szüneteken
    jobs = [
        Job(job_id="J1", due_date=1500, operations=[
            Operation(operation_id="J1_1", machine_id="M1", duration=200),
            Operation(operation_id="J1_2", machine_id="M2", duration=300),
            Operation(operation_id="J1_3", machine_id="M3", duration=150)
        ]),
        Job(job_id="J2", due_date=1500, operations=[
            Operation(operation_id="J2_1", machine_id="M2", duration=250),
            Operation(operation_id="J2_2", machine_id="M1", duration=300),
            Operation(operation_id="J2_3", machine_id="M3", duration=200)
        ]),
        Job(job_id="J3", due_date=2000, operations=[
            Operation(operation_id="J3_1", machine_id="M3", duration=100),
            Operation(operation_id="J3_2", machine_id="M1", duration=200),
            Operation(operation_id="J3_3", machine_id="M2", duration=350)
        ]),
        Job(job_id="J4", due_date=2000, release_time=100, operations=[
            Operation(operation_id="J4_1", machine_id="M1", duration=150),
            Operation(operation_id="J4_2", machine_id="M3", duration=100),
            Operation(operation_id="J4_3", machine_id="M2", duration=200)
        ])
    ]
    
    return jobs, machines

def run():
    print("\n--- 3. Mintapélda: Jó szint (Műszakok és rendelkezésre állás) ---")
    
    jobs, machines = get_shifts_data()
    sim = Simulator(jobs=jobs, machines=machines, dispatch_rule=fifo_rule)
    sim.run()
    
    evaluator = Evaluator()
    results = {"FIFO (Műszakokkal)": evaluator.calculate_metrics(jobs)}
    
    Visualizer.print_comparison_table(results)
    
    print("\n[!] Gantt-diagram generálása (figyeljük meg a szürke szünet blokkokat)...")
    Visualizer.plot_gantt_chart(jobs, machines, title="3. Példa - Műszakok (Szünetek szürkével)")

if __name__ == "__main__":
    run()
