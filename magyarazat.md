# Részletes Felkészülési Útmutató a Védéshez (Kódrészletekkel és Fájlszerkezettel)

Mivel a tanár úr a kód logikájára és a konkrét implementációra is kíváncsi lehet, ez a dokumentum úgy lett kibővítve, hogy **fájlról fájlra, függvényről függvényre** tudd elmagyarázni, hogyan épül fel a programod, és milyen Python specifikus megoldásokat (pl. `heapq`, `dataclasses`) használtál.

Így építsd fel a mondandódat:

---

## 1. A Projekt Fájlszerkezete és Architektúrája
"A projektet teljesen modulárisan építettem fel, hogy a különböző funkciók (adatok, szimuláció, ütemezés, kiértékelés) logikailag el legyenek különítve. Öt fő fájlom van:
1. `models.py`: Az alapvető adatstruktúrák és osztályok.
2. `simulator.py`: Maga az eseményvezérelt szimulációs motor.
3. `scheduler.py`: A reaktív ütemezési szabályok és a prediktív hegymászó (Hill Climbing) algoritmus.
4. `evaluator.py`: A teljesítménymutatók (Cmax, Tmax, stb.) kiszámítása.
5. `visualizer.py`: A Gantt-diagram rajzolása."

---

## 2. Az Adatmodellek (`models.py`)
"Az objektumok definiálásához a Python beépített `@dataclass` dekorátorát használtam, mert így sokkal tisztább és átláthatóbb lett a kód.
A főbb osztályaim:
- **`Operation`**: Egy adott műveletet ír le. Van benne `duration` (időtartam), `machine_id` és állapot (`status`: PENDING, IN_PROGRESS, DONE).
- **`Job`**: Egy munkadarabot reprezentál. Tartalmazza a műveletek listáját (`operations`), és egy `current_op_index` változót, amivel követem, hogy épp hol tart. Van egy property függvénye (`tardiness`), ami dinamikusan kiszámolja a késést a `due_date` alapján.
- **`Buffer`**: Egy egyszerű FIFO sor osztály. Ha meg van adva `capacity` (kapacitás), akkor az `enqueue` függvény `False`-szal tér vissza, ha a sor betelt.
- **`Machine`**: A gép osztálya. Tartalmaz egy `Buffer`-t, és egy `availability_windows` listát, ami a műszakok kezdő és végpontjait tárolja tuple-ök formájában.

Valamint itt definiáltam a legfontosabbat, a **`SimEvent`** osztályt, ami a prioritásos sorhoz kell:
```python
@dataclass(order=True)
class SimEvent:
    time: int
    priority: int
    event_type: EventType = field(compare=False)
    payload: dict = field(compare=False)
```
Ezt azért csináltam így, hogy a szimulátor automatikusan a `time` (időpont) alapján tudja sorba rendezni az eseményeket."

---

## 3. A Szimulációs Motor (`simulator.py`)
"A szimulátor lelke a `Simulator` osztály és annak a `run()` metódusa. Ez egy igazi **eseményvezérelt (discrete event)** motor. A háttérben a Python beépített `heapq` (min-heap) modulját használtam a prioritásos sor megvalósításához.

A főciklus így néz ki:
```python
while self.event_queue:
    event = heapq.heappop(self.event_queue)
    self.current_time = event.time
    # ... eseménytípus alapján hívom a megfelelő _handle_* függvényt
```

**Eseménykezelő függvények:**
- `_handle_job_arrival`: Amikor megérkezik a munka, megpróbálom betenni a gép pufferébe (`buffer.enqueue`). Ha sikerül, generálok egy `MACHINE_AVAILABLE` eseményt a gépnek.
- `_handle_machine_available`: Ez hívja meg az ütemezőt (pl. `self.dispatch_rule(machine.buffer.queue, self.current_time)`), kiveszi a kiválasztott munkát a pufferből, és elkezdi a feldolgozást. Létrehoz egy `OPERATION_COMPLETE` eseményt a jövőbe.
- `_handle_operation_complete`: Itt van a **blokkolás** logikája. Ha a munka kész, megpróbálja áttenni a következő gép pufferébe. Ha az tele van (a `buffer.enqueue` False-t ad), a jelenlegi gép belekerül egy `self.blocked_machines` szótárba, és nem tud új munkát felvenni.

**Blokkolás feloldása:**
Van egy `_check_blocked_machines` függvényem. Ezt mindig meghívom, amikor egy gép kivesz egy munkát a pufferéből (tehát felszabadult egy hely). Ez a függvény végignézi a blokkolt gépeket, és megpróbálja átnyomni az elakadt munkájukat. Ha sikerül, a gép kikerül a blokkolt állapotból."

---

## 4. Ütemező Algoritmusok (`scheduler.py`)
"Az ütemezőket egyszerű függvényekként írtam meg, amik kapnak egy listát a várakozó `Job`-okról, és visszaadják a nyertest. Például a Shortest Processing Time (SPT) szabály Pythonban nagyon röviden, lambdával megoldható volt:
```python
def spt_rule(queue: List[Job], current_time: int) -> Job:
    return min(queue, key=lambda j: j.get_current_operation().duration)
```

**A Prediktív Hegymászó (Hill Climbing) algoritmus:**
Ehhez írtam egy külön `PredictiveScheduler` osztályt. Az `optimize()` metódusa végzi a nehéz munkát.
- Először a `generate_initial_sequences()` csinál egy mohó (Earliest Due Date alapján rendezett) kezdeti sorrendet minden gépre.
- Utána egy `for` ciklusban (mondjuk 100 iteráción át) elkészítem az aktuális megoldás 'szomszédját' úgy, hogy a Python `random.sample` függvényével kiválasztok két munkát az egyik gép sorrendjéből, és kicserélem őket (swap).
- Ezt a szomszédos sorrendet kiszimulálom (ehhez a `copy.deepcopy`-t használom, hogy az eredeti adatokat ne rontsam el), és kiszámolom a Wmix pontszámot. Ha jobb (kisebb) az új pontszám, megtartom az új sorrendet."

---

## 5. Kiértékelés és Wmix (`evaluator.py`)
"Az `Evaluator` osztály végzi a metrikák számolását. A szimuláció végén végigiterál a munkákon:
- **Cmax (Makespan)**: A legnagyobb `completion_time` a munkák között (`max(cmax, job.completion_time)`).
- **Tmax (Max csúszás)**: Kikeresi a legnagyobb `tardiness` értéket.
- Végül kiszámolja a súlyozott összeget (`Wmix`):
```python
wmix = self.w1 * cmax + self.w2 * tmax + self.w3 * sum_ti + self.w4 * nt
```
Ezt a `Wmix` értéket használja a Hill Climbing algoritmus a minimalizáláshoz."

---

## Összefoglaló a tanár számára (Hogyan zárd le):
"Összességében a szoftvert úgy terveztem meg, hogy az események (SimEvent) irányítsanak mindent egy min-heap adatszerkezeten keresztül (`heapq`). Az adatokat Python Dataclass-okban tárolom a tisztább kód érdekében. A pufferek korlátozását egy egyszerű if-else ággal és egy blokkolási szótárral (`blocked_machines`) oldottam meg az eseménykezelőn belül. A prediktív algoritmusom pedig a háttérben deepcopy-val klónozott szimulációkat futtat, és folyamatosan cserélgetve a feladatok sorrendjét keresi a legkisebb `Wmix` értékkel rendelkező ütemtervet."
