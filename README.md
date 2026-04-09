# Processor Design Task 3

This project implements Task 3 of the CSC 4210/6210 Computer Architecture processor design project.

## Overview

The program simulates a processor memory hierarchy using SSD, DRAM, L3, L2, and L1. It enforces hierarchical data movement, supports read and write operations, tracks the clock cycle for every transfer, and includes the bonus cache replacement policies.

## Features

- Simulates the hierarchy `SSD -> DRAM -> L3 -> L2 -> L1 -> CPU`
- Prevents direct access that bypasses intermediate levels
- Treats all values as 32-bit instructions
- Allows configurable sizes for SSD, DRAM, L3, L2, and L1
- Allows configurable latencies and transfer bandwidth
- Supports `READ` and `WRITE` operations
- Uses a clock-driven simulation model
- Logs movement of data across levels
- Tracks cache hits and misses
- Prints the final state of every level
- Includes the bonus replacement policies: `LRU`, `FIFO`, and `RANDOM`

## Requirements

- Python 3

## Run With a Trace File

```bash
python3 'Processor(3).py' --trace task3_trace.txt
```

## Run With Interactive Input

```bash
python3 'Processor(3).py'
```

Enter operations one per line:

```text
READ <address>
WRITE <address> <value>
```

Type `DONE` when finished.

## Example Trace File

```text
READ 0
READ 1
READ 0
WRITE 2 0x12345678
READ 2
WRITE 5 255
READ 5
```

## Example With Custom Parameters

```bash
python3 'Processor(3).py' \
  --ssd-size 16 \
  --dram-size 8 \
  --l3-size 4 \
  --l2-size 3 \
  --l1-size 2 \
  --ssd-latency 10 \
  --dram-latency 6 \
  --l3-latency 3 \
  --l2-latency 2 \
  --l1-latency 1 \
  --bandwidth 1 \
  --policy LRU \
  --trace task3_trace.txt
```

## Program Output

The program prints:

1. Memory hierarchy configuration
2. Instruction access trace
3. Movement of data across levels
4. Cache hits and misses
5. Final state of each memory level
