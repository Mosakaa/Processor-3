# Hafeez Imran

import argparse
import math
import random
from collections import OrderedDict


class MemoryLevel:
    def __init__(self, name, capacity, latency, bandwidth=1, replacement_policy="FIFO"):
        self.name = name
        self.capacity = capacity
        self.latency = latency
        self.bandwidth = bandwidth
        self.replacement_policy = replacement_policy
        self.storage = OrderedDict()
        self.random_generator = random.Random(4210)

    def contains(self, address):
        return address in self.storage

    def read(self, address, update_recency=True):
        entry = self.storage[address]
        if update_recency and self.replacement_policy == "LRU":
            self.storage.move_to_end(address)
        return dict(entry)

    def write(self, address, value, dirty=False, update_recency=True):
        entry = {"value": value, "dirty": dirty}
        self.storage[address] = entry
        if update_recency and self.replacement_policy in ("LRU", "FIFO"):
            self.storage.move_to_end(address)

    def is_full(self):
        return len(self.storage) >= self.capacity

    def choose_eviction_address(self):
        if self.replacement_policy in ("FIFO", "LRU"):
            return next(iter(self.storage))

        addresses = list(self.storage.keys())
        return self.random_generator.choice(addresses)

    def evict(self):
        if not self.storage:
            return None

        address = self.choose_eviction_address()
        entry = self.storage.pop(address)
        return {"address": address, "value": entry["value"], "dirty": entry["dirty"]}

    def dirty_entries(self):
        return [
            {"address": address, "value": entry["value"], "dirty": entry["dirty"]}
            for address, entry in self.storage.items()
            if entry["dirty"]
        ]

    def snapshot_lines(self):
        if not self.storage:
            return ["(empty)"]

        lines = []
        for address, entry in self.storage.items():
            dirty_marker = " dirty" if entry["dirty"] else " clean"
            lines.append(f"Addr {address:>3}: {entry['value']} ({dirty_marker.strip()})")
        return lines


class Processor:
    def __init__(self):
        self.level_order = ["L1", "L2", "L3", "DRAM", "SSD"]
        self.levels = {}
        self.clock = 0
        self.operations = []
        self.movement_log = []
        self.access_log = []
        self.cache_stats = {
            "L1": {"hits": 0, "misses": 0},
            "L2": {"hits": 0, "misses": 0},
            "L3": {"hits": 0, "misses": 0}
        }

    def run(self):
        args = self._parse_arguments()

        self._validate_hierarchy(args)
        self._build_memory_hierarchy(args)
        self.operations = self._get_operations(args.trace)

        self._print_configuration(args)
        self._execute_operations()
        self._flush_dirty_data()
        self._print_summary()

    def _parse_arguments(self):
        parser = argparse.ArgumentParser(
            description="Task 3: Memory Hierarchy Simulation (SSD -> DRAM -> Cache)"
        )
        parser.add_argument("--ssd-size", type=int, default=32, help="SSD capacity in instructions")
        parser.add_argument("--dram-size", type=int, default=16, help="DRAM capacity in instructions")
        parser.add_argument("--l3-size", type=int, default=8, help="L3 cache capacity in instructions")
        parser.add_argument("--l2-size", type=int, default=4, help="L2 cache capacity in instructions")
        parser.add_argument("--l1-size", type=int, default=2, help="L1 cache capacity in instructions")
        parser.add_argument("--ssd-latency", type=int, default=12, help="SSD access latency in cycles")
        parser.add_argument("--dram-latency", type=int, default=6, help="DRAM access latency in cycles")
        parser.add_argument("--l3-latency", type=int, default=3, help="L3 access latency in cycles")
        parser.add_argument("--l2-latency", type=int, default=2, help="L2 access latency in cycles")
        parser.add_argument("--l1-latency", type=int, default=1, help="L1 access latency in cycles")
        parser.add_argument("--bandwidth", type=int, default=1, help="Instructions transferred per cycle")
        parser.add_argument(
            "--policy",
            choices=["LRU", "FIFO", "RANDOM"],
            default="LRU",
            help="Bonus cache replacement policy used by L1, L2, and L3"
        )
        parser.add_argument(
            "--trace",
            help="Optional path to a trace file. If omitted, the program will prompt for operations."
        )

        return parser.parse_args()

    def _validate_hierarchy(self, args):
        sizes = [args.ssd_size, args.dram_size, args.l3_size, args.l2_size, args.l1_size]
        if any(size <= 0 for size in sizes):
            raise ValueError("All memory sizes must be positive integers.")

        if not (args.ssd_size > args.dram_size > args.l3_size > args.l2_size > args.l1_size):
            raise ValueError("The hierarchy must satisfy: SSD > DRAM > L3 > L2 > L1.")

        latencies = [
            args.ssd_latency,
            args.dram_latency,
            args.l3_latency,
            args.l2_latency,
            args.l1_latency
        ]
        if any(latency <= 0 for latency in latencies):
            raise ValueError("All latencies must be positive integers.")

        if args.bandwidth <= 0:
            raise ValueError("Bandwidth must be a positive integer.")

    def _build_memory_hierarchy(self, args):
        self.levels["L1"] = MemoryLevel("L1", args.l1_size, args.l1_latency, args.bandwidth, args.policy)
        self.levels["L2"] = MemoryLevel("L2", args.l2_size, args.l2_latency, args.bandwidth, args.policy)
        self.levels["L3"] = MemoryLevel("L3", args.l3_size, args.l3_latency, args.bandwidth, args.policy)
        self.levels["DRAM"] = MemoryLevel("DRAM", args.dram_size, args.dram_latency, args.bandwidth, "FIFO")
        self.levels["SSD"] = MemoryLevel("SSD", args.ssd_size, args.ssd_latency, args.bandwidth, "FIFO")

        for address in range(args.ssd_size):
            self.levels["SSD"].write(address, self._format_instruction(address), dirty=False)

    def _format_instruction(self, value):
        return f"0x{value & 0xFFFFFFFF:08X}"

    def _normalize_instruction(self, raw_value):
        try:
            value = int(raw_value, 0)
        except ValueError as error:
            raise ValueError(f"Invalid instruction value: {raw_value}") from error

        if value < 0 or value > 0xFFFFFFFF:
            raise ValueError("All instructions must fit in 32 bits (0 to 0xFFFFFFFF).")

        return self._format_instruction(value)

    def _get_operations(self, trace_path=None):
        if trace_path:
            with open(trace_path, "r", encoding="utf-8") as trace_file:
                raw_lines = [line.strip() for line in trace_file if line.strip()]
        else:
            print("Enter one operation per line in the format: READ <address> or WRITE <address> <value>")
            print("Type DONE when finished.")

            raw_lines = []
            while True:
                line = input("Operation: ").strip()
                if line.upper() == "DONE":
                    break
                if line:
                    raw_lines.append(line)

        if not raw_lines:
            raise ValueError("At least one operation is required.")

        operations = []
        for line_number, line in enumerate(raw_lines, start=1):
            operations.append(self._parse_operation(line, line_number))

        return operations

    def _parse_operation(self, line, line_number):
        parts = line.split()
        operation = parts[0].upper()

        if operation == "READ" and len(parts) == 2:
            address = self._parse_address(parts[1], line_number)
            return {"type": "READ", "address": address}

        if operation == "WRITE" and len(parts) == 3:
            address = self._parse_address(parts[1], line_number)
            value = self._normalize_instruction(parts[2])
            return {"type": "WRITE", "address": address, "value": value}

        raise ValueError(
            f"Invalid operation at line {line_number}. Use READ <address> or WRITE <address> <value>."
        )

    def _parse_address(self, raw_address, line_number):
        try:
            address = int(raw_address, 0)
        except ValueError as error:
            raise ValueError(f"Invalid address at line {line_number}: {raw_address}") from error

        if address < 0 or address >= self.levels["SSD"].capacity:
            raise ValueError(
                f"Address out of range at line {line_number}: {address}. Valid range is 0 to "
                f"{self.levels['SSD'].capacity - 1}."
            )

        return address

    def _print_configuration(self, args):
        print("Memory Hierarchy Configuration")
        print("------------------------------")
        print(f"SSD  : size={args.ssd_size} instructions, latency={args.ssd_latency} cycles")
        print(f"DRAM : size={args.dram_size} instructions, latency={args.dram_latency} cycles")
        print(f"L3   : size={args.l3_size} instructions, latency={args.l3_latency} cycles")
        print(f"L2   : size={args.l2_size} instructions, latency={args.l2_latency} cycles")
        print(f"L1   : size={args.l1_size} instructions, latency={args.l1_latency} cycles")
        print(f"Bandwidth: {args.bandwidth} instruction(s) per cycle")
        print(f"Cache replacement policy: {args.policy}")

    def _execute_operations(self):
        print("\nInstruction Access Trace")
        print("------------------------")

        for index, operation in enumerate(self.operations, start=1):
            if operation["type"] == "READ":
                result = self._handle_read(operation["address"])
                print(
                    f"{index:>2}. READ  addr={operation['address']:>2} -> {result['value']} "
                    f"(completed at cycle {result['cycle']})"
                )
                self.access_log.append(
                    {
                        "operation": "READ",
                        "address": operation["address"],
                        "value": result["value"],
                        "cycle": result["cycle"]
                    }
                )
            else:
                result = self._handle_write(operation["address"], operation["value"])
                print(
                    f"{index:>2}. WRITE addr={operation['address']:>2} <- {operation['value']} "
                    f"(completed at cycle {result['cycle']})"
                )
                self.access_log.append(
                    {
                        "operation": "WRITE",
                        "address": operation["address"],
                        "value": operation["value"],
                        "cycle": result["cycle"]
                    }
                )

    def _handle_read(self, address):
        value = self._fetch_to_l1(address)
        self._advance_clock("L1", "CPU", address, value, "Read serviced to CPU")
        return {"value": value, "cycle": self.clock}

    def _handle_write(self, address, value):
        self._fetch_to_l1(address)
        self._advance_clock("CPU", "L1", address, value, "CPU write into L1")
        self.levels["L1"].write(address, value, dirty=True)
        return {"cycle": self.clock}

    def _fetch_to_l1(self, address):
        source_name = None
        found_entry = None

        for level_name in self.level_order:
            level = self.levels[level_name]

            if level_name in self.cache_stats:
                if level.contains(address):
                    self.cache_stats[level_name]["hits"] += 1
                else:
                    self.cache_stats[level_name]["misses"] += 1

            if level.contains(address):
                source_name = level_name
                found_entry = level.read(address, update_recency=(level_name in self.cache_stats))
                break

        value = found_entry["value"]

        promotion_path = self._path_to_l1(source_name)
        for from_level, to_level in promotion_path:
            self._move_value_up(from_level, to_level, address, value)

        return value

    def _path_to_l1(self, source_name):
        paths = {
            "L1": [],
            "L2": [("L2", "L1")],
            "L3": [("L3", "L2"), ("L2", "L1")],
            "DRAM": [("DRAM", "L3"), ("L3", "L2"), ("L2", "L1")],
            "SSD": [("SSD", "DRAM"), ("DRAM", "L3"), ("L3", "L2"), ("L2", "L1")]
        }
        return paths[source_name]

    def _move_value_up(self, from_level_name, to_level_name, address, value):
        self._advance_clock(from_level_name, to_level_name, address, value, "Hierarchical promotion")
        self._store_in_level(to_level_name, address, value, dirty=False)

    def _store_in_level(self, level_name, address, value, dirty):
        level = self.levels[level_name]

        if level.contains(address):
            existing_entry = level.read(address, update_recency=False)
            level.write(address, value, dirty=dirty or existing_entry["dirty"])
            return

        if level.is_full():
            evicted_entry = level.evict()
            self._record_eviction(level_name, evicted_entry)

        level.write(address, value, dirty=dirty)

    def _record_eviction(self, level_name, evicted_entry):
        self.movement_log.append(
            f"Cycle {self.clock:>3}: Evict {self._format_entry(evicted_entry)} from {level_name}"
        )

        if not evicted_entry["dirty"]:
            return

        lower_level_name = self._lower_level(level_name)
        if lower_level_name is None:
            return

        self._advance_clock(
            level_name,
            lower_level_name,
            evicted_entry["address"],
            evicted_entry["value"],
            "Dirty write-back after eviction"
        )
        self._store_in_level(
            lower_level_name,
            evicted_entry["address"],
            evicted_entry["value"],
            dirty=(lower_level_name != "SSD")
        )

    def _lower_level(self, level_name):
        lower_map = {"L1": "L2", "L2": "L3", "L3": "DRAM", "DRAM": "SSD", "SSD": None}
        return lower_map[level_name]

    def _advance_clock(self, from_level, to_level, address, value, reason):
        transfer_cycles = self._transfer_cycles(from_level, to_level)
        start_cycle = self.clock + 1
        self.clock += transfer_cycles
        self.movement_log.append(
            f"Cycle {start_cycle:>3}-{self.clock:>3}: {from_level} -> {to_level} | "
            f"Addr {address:>3} | {value} | {reason}"
        )

    def _transfer_cycles(self, from_level, to_level):
        if from_level == "CPU":
            base_latency = self.levels[to_level].latency
        elif to_level == "CPU":
            base_latency = self.levels[from_level].latency
        else:
            base_latency = max(self.levels[from_level].latency, self.levels[to_level].latency)

        transfer_time = math.ceil(1 / self.levels["L1"].bandwidth)
        return base_latency + transfer_time - 1

    def _flush_dirty_data(self):
        print("\nFlushing Dirty Data")
        print("-------------------")

        dirty_data_found = False
        for level_name in ["L1", "L2", "L3", "DRAM"]:
            level = self.levels[level_name]
            for entry in list(level.dirty_entries()):
                dirty_data_found = True
                lower_level_name = self._lower_level(level_name)
                self._advance_clock(
                    level_name,
                    lower_level_name,
                    entry["address"],
                    entry["value"],
                    "Final flush write-back"
                )
                level.write(entry["address"], entry["value"], dirty=False)
                self._store_in_level(
                    lower_level_name,
                    entry["address"],
                    entry["value"],
                    dirty=(lower_level_name != "SSD")
                )

        if not dirty_data_found:
            print("No dirty data to flush.")
        else:
            for line in self.movement_log:
                if "Final flush write-back" in line:
                    print(line)

    def _print_summary(self):
        print("\nMovement of Data Across Levels")
        print("------------------------------")
        for line in self.movement_log:
            print(line)

        print("\nCache Hits / Misses")
        print("-------------------")
        for cache_name in ["L1", "L2", "L3"]:
            hits = self.cache_stats[cache_name]["hits"]
            misses = self.cache_stats[cache_name]["misses"]
            print(f"{cache_name}: hits={hits}, misses={misses}")

        print("\nFinal State of Each Memory Level")
        print("-------------------------------")
        for level_name in ["L1", "L2", "L3", "DRAM", "SSD"]:
            print(level_name)
            for line in self.levels[level_name].snapshot_lines():
                print(line)
            print()

    def _format_entry(self, entry):
        dirty_marker = "dirty" if entry["dirty"] else "clean"
        return f"Addr {entry['address']} | {entry['value']} | {dirty_marker}"


processor = Processor()
processor.run()