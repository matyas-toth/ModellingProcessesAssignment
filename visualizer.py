import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import random
from typing import List, Dict
from models import Job, Machine

class Visualizer:
    """
    Az eredmények megjelenítéséért felelős modul.
    """
    @staticmethod
    def plot_gantt_chart(jobs: List[Job], machines: Dict[str, Machine], title: str = "Gantt-diagram"):
        """Gantt-diagramot rajzol a szimulált munkákból és a gép-rendelkezésre állásokból."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Gép nevek az Y tengelyen
        machine_ids = list(machines.keys())
        y_ticks = range(len(machine_ids))
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(machine_ids)
        
        # Színek generálása a munkákhoz
        colors = plt.cm.get_cmap('tab20', len(jobs))
        job_colors = {job.job_id: colors(i) for i, job in enumerate(jobs)}
        
        max_time = 0
        
        # Először kirajzoljuk a műszakon kívüli (szünet) sávokat szürkével
        for i, m_id in enumerate(machine_ids):
            machine = machines[m_id]
            if machine.availability_windows:
                # Keresünk egy maximum időt a rajzoláshoz
                temp_max = max((end for _, end in machine.availability_windows), default=0)
                max_time = max(max_time, temp_max)
                
                # A szünetek a műszakok közötti időszakok
                last_end = 0
                for start, end in sorted(machine.availability_windows):
                    if start > last_end:
                        # Szünet kirajzolása
                        ax.barh(i, start - last_end, left=last_end, color='lightgray', hatch='//')
                    last_end = end
                
                # Ha a max_time nagyobb, mint a legutolsó műszak vége, a maradék is szünet
                # De ezt majd a műveletek max ideje alapján pontosítjuk
        
        # Műveletek (blokkok) kirajzolása
        for job in jobs:
            for op in job.operations:
                if op.start_time is not None and op.end_time is not None:
                    m_idx = machine_ids.index(op.machine_id)
                    ax.barh(
                        m_idx, 
                        op.end_time - op.start_time, 
                        left=op.start_time, 
                        color=job_colors[job.job_id], 
                        edgecolor='black'
                    )
                    
                    # Művelet és munka azonosító ráírása a blokkra
                    ax.text(
                        op.start_time + (op.end_time - op.start_time) / 2, 
                        m_idx, 
                        f"{job.job_id}", 
                        ha='center', va='center', color='white', fontweight='bold', fontsize=8
                    )
                    max_time = max(max_time, op.end_time)
                    
            # Határidő jelzése egy függőleges vonallal (ha a diagram tartományába esik)
            if job.due_date <= max_time * 1.2:
                ax.axvline(x=job.due_date, color=job_colors[job.job_id], linestyle='--', alpha=0.6)
                
        # Tengelyek és címkék beállítása
        ax.set_xlabel("Idő")
        ax.set_ylabel("Gépek")
        ax.set_title(title)
        
        # Jelmagyarázat
        patches = [mpatches.Patch(color=job_colors[job.job_id], label=f"{job.job_id} (határidő: {job.due_date})") for job in jobs]
        patches.append(mpatches.Patch(color='lightgray', hatch='//', label='Műszakon kívül (szünet)'))
        ax.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        plt.grid(axis='x', linestyle=':', alpha=0.7)
        plt.show()

    @staticmethod
    def print_comparison_table(results: Dict[str, Dict[str, float]]):
        """Különböző ütemezési stratégiák eredményeit hasonlítja össze táblázatos formában."""
        print("-" * 75)
        print(f"{'Stratégia':<20} | {'Cmax':<8} | {'Tmax':<8} | {'Sum(Ti)':<8} | {'NT':<4} | {'Wmix':<8}")
        print("-" * 75)
        
        for strategy, metrics in results.items():
            print(f"{strategy:<20} | "
                  f"{metrics.get('Cmax', 0):<8.2f} | "
                  f"{metrics.get('Tmax', 0):<8.2f} | "
                  f"{metrics.get('SumTi', 0):<8.2f} | "
                  f"{metrics.get('NT', 0):<4.0f} | "
                  f"{metrics.get('Wmix', 0):<8.2f}")
        print("-" * 75)
