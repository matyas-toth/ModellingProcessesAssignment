import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Job, Operation, Machine
from simulator import Simulator
from scheduler import fifo_rule
from evaluator import Evaluator
from visualizer import Visualizer

def get_buffer_data(capacity=None):
    """
    2. példa – Közepes szint:
    5 munka, 4 gép. Beállítható a pufferek kapacitása (pl. 2 vagy None/végtelen).
    """
    machines = {
        f"M{i}": Machine(f"M{i}", capacity=capacity) for i in range(1, 5)
    }

    jobs = [
        Job(job_id="J1", due_date=30, release_time=0, operations=[
            Operation(operation_id="J1_1", machine_id="M1", duration=4),
            Operation(operation_id="J1_2", machine_id="M2", duration=3),
            Operation(operation_id="J1_3", machine_id="M4", duration=2)
        ]),
        Job(job_id="J2", due_date=30, release_time=1, operations=[
            Operation(operation_id="J2_1", machine_id="M1", duration=5),
            Operation(operation_id="J2_2", machine_id="M3", duration=4),
            Operation(operation_id="J2_3", machine_id="M4", duration=3)
        ]),
        Job(job_id="J3", due_date=30, release_time=2, operations=[
            Operation(operation_id="J3_1", machine_id="M1", duration=3),
            Operation(operation_id="J3_2", machine_id="M2", duration=6),
            Operation(operation_id="J3_3", machine_id="M3", duration=4)
        ]),
        Job(job_id="J4", due_date=40, release_time=3, operations=[
            Operation(operation_id="J4_1", machine_id="M2", duration=4),
            Operation(operation_id="J4_2", machine_id="M1", duration=3),
            Operation(operation_id="J4_3", machine_id="M4", duration=5)
        ]),
        Job(job_id="J5", due_date=40, release_time=4, operations=[
            Operation(operation_id="J5_1", machine_id="M3", duration=2),
            Operation(operation_id="J5_2", machine_id="M2", duration=5),
            Operation(operation_id="J5_3", machine_id="M4", duration=4)
        ])
    ]
    
    return jobs, machines

def run():
    print("\n--- 2. Mintapélda: Közepes szint (Korlátozott pufferek) ---")
    evaluator = Evaluator()
    results = {}

    # 1. Végtelen puffer szimulációja
    jobs_inf, machines_inf = get_buffer_data(capacity=None)
    sim_inf = Simulator(jobs=jobs_inf, machines=machines_inf, dispatch_rule=fifo_rule)
    sim_inf.run()
    results["FIFO (Végtelen puffer)"] = evaluator.calculate_metrics(jobs_inf)

    # 2. Korlátozott puffer (2) szimulációja
    jobs_lim, machines_lim = get_buffer_data(capacity=2)
    sim_lim = Simulator(jobs=jobs_lim, machines=machines_lim, dispatch_rule=fifo_rule)
    sim_lim.run()
    results["FIFO (Kapacitás = 2)"] = evaluator.calculate_metrics(jobs_lim)

    Visualizer.print_comparison_table(results)
    
    print("\n[!] Gantt-diagram generálása a KORLÁTOZOTT pufferű (blokkolásos) állapothoz...")
    Visualizer.plot_gantt_chart(jobs_lim, machines_lim, title="2. Példa - Korlátozott Puffer (Kapacitás=2)")

if __name__ == "__main__":
    run()
