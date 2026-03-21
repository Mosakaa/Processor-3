# Hafeez Imran

import argparse


class Processor:
    def __init__(self):
        self.variable_names = [chr(ord('A') + i) for i in range(26)]

    def run(self):
        args = self._parse_arguments()

        if args.num_variables > len(self.variable_names):
            raise ValueError("This program supports up to 26 input variables.")

        truth_table = self._get_truth_table(args.num_variables, args.file)
        output_data = self._build_output_data(args.num_variables, truth_table, args.form)

        self._print_truth_table(args.num_variables, truth_table)
        self._print_results(output_data)

    def _parse_arguments(self):
        parser = argparse.ArgumentParser(
            description="Task 2: Truth Table -> Boolean Equation -> K-Map Simplification"
        )
        parser.add_argument("num_variables", type=int, help="Number of input variables (n >= 2)")
        parser.add_argument(
            "--form",
            choices=["SOP", "POS"],
            default="SOP",
            help="Canonical form to generate"
        )
        parser.add_argument(
            "--file",
            help="Optional path to a truth table file. If omitted, the program will prompt for input."
        )

        args = parser.parse_args()

        if args.num_variables < 2:
            raise ValueError("The number of input variables must be at least 2.")

        return args

    def _get_truth_table(self, num_variables, file_path=None):
        row_count = 1 << num_variables
        rows = []

        if file_path:
            with open(file_path, "r", encoding="utf-8") as input_file:
                for line_number, raw_line in enumerate(input_file, start=1):
                    line = raw_line.strip()
                    if not line:
                        continue
                    rows.append(self._parse_row(line, num_variables, line_number))
        else:
            print(f"Enter {row_count} truth table rows in the format: <bits> <output>")
            print(f"Example for n={num_variables}: {'0' * num_variables} 0")

            for row_index in range(row_count):
                user_line = input(f"Row {row_index + 1}/{row_count}: ").strip()
                rows.append(self._parse_row(user_line, num_variables, row_index + 1))

        return self._validate_truth_table(num_variables, rows)

    def _parse_row(self, line, num_variables, line_number):
        parts = line.split()

        if len(parts) == 2 and len(parts[0]) == num_variables and parts[1] in ("0", "1"):
            bits = parts[0]
            output = parts[1]
        elif len(parts) == num_variables + 1 and all(part in ("0", "1") for part in parts):
            bits = "".join(parts[:-1])
            output = parts[-1]
        else:
            raise ValueError(
                f"Invalid row at line {line_number}. Use either '<bits> <output>' or separated binary digits."
            )

        if any(bit not in ("0", "1") for bit in bits):
            raise ValueError(f"Invalid input combination at line {line_number}. Inputs must contain only 0 or 1.")

        if output not in ("0", "1"):
            raise ValueError(f"Invalid output at line {line_number}. Output values must be 0 or 1.")

        return bits, int(output)

    def _validate_truth_table(self, num_variables, rows):
        expected_count = 1 << num_variables

        if len(rows) != expected_count:
            raise ValueError(f"The truth table must contain exactly {expected_count} rows.")

        truth_table = {}

        for bits, output in rows:
            if bits in truth_table:
                raise ValueError(f"Duplicate input combination found: {bits}")
            truth_table[bits] = output

        expected_inputs = {format(index, f"0{num_variables}b") for index in range(expected_count)}
        provided_inputs = set(truth_table.keys())

        if provided_inputs != expected_inputs:
            missing_inputs = sorted(expected_inputs - provided_inputs)
            extra_inputs = sorted(provided_inputs - expected_inputs)

            error_parts = []
            if missing_inputs:
                error_parts.append(f"missing combinations: {', '.join(missing_inputs)}")
            if extra_inputs:
                error_parts.append(f"invalid combinations: {', '.join(extra_inputs)}")

            raise ValueError("Truth table validation failed: " + "; ".join(error_parts))

        return truth_table

    def _build_output_data(self, num_variables, truth_table, form):
        variables = self.variable_names[:num_variables]
        ordered_inputs = [format(index, f"0{num_variables}b") for index in range(1 << num_variables)]

        if form == "SOP":
            selected_terms = [index for index, bits in enumerate(ordered_inputs) if truth_table[bits] == 1]
        else:
            selected_terms = [index for index, bits in enumerate(ordered_inputs) if truth_table[bits] == 0]

        canonical_expression = self._build_canonical_expression(num_variables, form, selected_terms)
        simplified_implicants = self._find_simplified_implicants(num_variables, selected_terms)
        simplified_expression = self._build_simplified_expression(variables, simplified_implicants, form, selected_terms)
        kmap_groups = self._build_kmap_groups(simplified_implicants, form, variables, selected_terms)
        validation_passed = self._validate_simplified_expression(
            num_variables,
            truth_table,
            simplified_implicants,
            form,
            selected_terms
        )

        return {
            "form": form,
            "canonical_expression": canonical_expression,
            "term_list": selected_terms,
            "kmap": self._build_kmap(num_variables, truth_table),
            "kmap_groups": kmap_groups,
            "simplified_expression": simplified_expression,
            "validation_result": "PASS" if validation_passed else "FAIL"
        }

    def _build_canonical_expression(self, num_variables, form, terms):
        variables = self.variable_names[:num_variables]

        if form == "SOP":
            if not terms:
                return "F = 0"
            expression_parts = []
            for term in terms:
                bits = format(term, f"0{num_variables}b")
                product = []
                for index, bit in enumerate(bits):
                    if bit == "1":
                        product.append(variables[index])
                    else:
                        product.append(f"{variables[index]}'")
                expression_parts.append("".join(product))
            return "F = " + " + ".join(expression_parts)

        if len(terms) == 1 << num_variables:
            return "F = 0"
        if not terms:
            return "F = 1"

        expression_parts = []
        for term in terms:
            bits = format(term, f"0{num_variables}b")
            sum_part = []
            for index, bit in enumerate(bits):
                if bit == "1":
                    sum_part.append(f"{variables[index]}'")
                else:
                    sum_part.append(variables[index])
            expression_parts.append("(" + " + ".join(sum_part) + ")")

        return "F = " + "".join(expression_parts)

    def _find_simplified_implicants(self, num_variables, terms):
        if not terms:
            return []

        all_terms = list(range(1 << num_variables))
        if len(terms) == len(all_terms):
            return [{"pattern": "-" * num_variables, "terms": set(all_terms)}]

        current_groups = []
        for term in sorted(terms):
            current_groups.append({
                "pattern": format(term, f"0{num_variables}b"),
                "terms": {term}
            })

        prime_implicants = []

        while current_groups:
            next_groups = []
            used_patterns = set()
            combined_indexes = set()

            for left_index in range(len(current_groups)):
                for right_index in range(left_index + 1, len(current_groups)):
                    left_group = current_groups[left_index]
                    right_group = current_groups[right_index]
                    combined_pattern = self._combine_patterns(left_group["pattern"], right_group["pattern"])

                    if combined_pattern is not None:
                        combined_indexes.add(left_index)
                        combined_indexes.add(right_index)

                        pattern_key = (combined_pattern, tuple(sorted(left_group["terms"] | right_group["terms"])))
                        if pattern_key not in used_patterns:
                            used_patterns.add(pattern_key)
                            next_groups.append({
                                "pattern": combined_pattern,
                                "terms": left_group["terms"] | right_group["terms"]
                            })

            for index, group in enumerate(current_groups):
                if index not in combined_indexes:
                    prime_implicants.append(group)

            current_groups = next_groups

        filtered_prime_implicants = []
        seen_patterns = set()

        for implicant in prime_implicants:
            pattern_key = (implicant["pattern"], tuple(sorted(implicant["terms"])))
            if pattern_key not in seen_patterns:
                seen_patterns.add(pattern_key)
                filtered_prime_implicants.append(implicant)

        return self._select_covering_implicants(terms, filtered_prime_implicants)

    def _combine_patterns(self, left_pattern, right_pattern):
        difference_count = 0
        combined = []

        for left_bit, right_bit in zip(left_pattern, right_pattern):
            if left_bit == right_bit:
                combined.append(left_bit)
            elif left_bit != right_bit and left_bit != "-" and right_bit != "-":
                difference_count += 1
                combined.append("-")
            else:
                return None

            if difference_count > 1:
                return None

        if difference_count == 1:
            return "".join(combined)

        return None

    def _select_covering_implicants(self, terms, prime_implicants):
        uncovered_terms = set(terms)
        selected_implicants = []

        while True:
            essential_implicant = None

            for term in sorted(uncovered_terms):
                covering_implicants = [implicant for implicant in prime_implicants if term in implicant["terms"]]
                if len(covering_implicants) == 1:
                    essential_implicant = covering_implicants[0]
                    break

            if essential_implicant is None:
                break

            if essential_implicant not in selected_implicants:
                selected_implicants.append(essential_implicant)
            uncovered_terms -= essential_implicant["terms"]

        while uncovered_terms:
            best_implicant = max(
                prime_implicants,
                key=lambda implicant: (
                    len(implicant["terms"] & uncovered_terms),
                    implicant["pattern"].count("-"),
                    -implicant["pattern"].count("0") - implicant["pattern"].count("1")
                )
            )
            selected_implicants.append(best_implicant)
            uncovered_terms -= best_implicant["terms"]

        selected_implicants.sort(key=lambda implicant: (min(implicant["terms"]), implicant["pattern"]))
        return selected_implicants

    def _build_simplified_expression(self, variables, implicants, form, terms):
        variable_count = len(variables)

        if form == "SOP":
            if not terms:
                return "F = 0"
            if len(terms) == 1 << variable_count:
                return "F = 1"

            expression_parts = []
            for implicant in implicants:
                product = []
                for index, bit in enumerate(implicant["pattern"]):
                    if bit == "1":
                        product.append(variables[index])
                    elif bit == "0":
                        product.append(f"{variables[index]}'")

                expression_parts.append("".join(product) if product else "1")

            return "F = " + " + ".join(expression_parts)

        if not terms:
            return "F = 1"
        if len(terms) == 1 << variable_count:
            return "F = 0"

        expression_parts = []
        for implicant in implicants:
            sum_part = []
            for index, bit in enumerate(implicant["pattern"]):
                if bit == "1":
                    sum_part.append(f"{variables[index]}'")
                elif bit == "0":
                    sum_part.append(variables[index])

            expression_parts.append("(" + " + ".join(sum_part) + ")" if sum_part else "(0)")

        return "F = " + "".join(expression_parts)

    def _validate_simplified_expression(self, num_variables, truth_table, implicants, form, terms):
        all_inputs = [format(index, f"0{num_variables}b") for index in range(1 << num_variables)]

        for bits in all_inputs:
            expected = truth_table[bits]
            actual = self._evaluate_implicants(bits, implicants, form, terms, num_variables)
            if actual != expected:
                return False

        return True

    def _evaluate_implicants(self, bits, implicants, form, terms, num_variables):
        if form == "SOP":
            if not terms:
                return 0
            if len(terms) == 1 << num_variables:
                return 1

            for implicant in implicants:
                if self._pattern_matches(bits, implicant["pattern"]):
                    return 1
            return 0

        if not terms:
            return 1
        if len(terms) == 1 << num_variables:
            return 0

        for implicant in implicants:
            if self._pattern_matches(bits, implicant["pattern"]):
                return 0
        return 1

    def _pattern_matches(self, bits, pattern):
        for bit, pattern_bit in zip(bits, pattern):
            if pattern_bit != "-" and bit != pattern_bit:
                return False
        return True

    def _build_kmap(self, num_variables, truth_table):
        if num_variables == 2:
            row_labels = ["0", "1"]
            column_labels = ["0", "1"]
            row_bits = ["0", "1"]
            column_bits = ["0", "1"]
        elif num_variables == 3:
            row_labels = ["0", "1"]
            column_labels = ["00", "01", "11", "10"]
            row_bits = ["0", "1"]
            column_bits = ["00", "01", "11", "10"]
        elif num_variables == 4:
            row_labels = ["00", "01", "11", "10"]
            column_labels = ["00", "01", "11", "10"]
            row_bits = ["00", "01", "11", "10"]
            column_bits = ["00", "01", "11", "10"]
        else:
            return ["K-Map is only displayed for 2 to 4 variables."]

        output_lines = []
        header = " " * 10 + " | ".join(column_labels)
        output_lines.append(header)
        output_lines.append("-" * len(header))

        for row_label, row_value in zip(row_labels, row_bits):
            row_outputs = []
            for column_value in column_bits:
                bits = row_value + column_value
                row_outputs.append(str(truth_table[bits]))
            output_lines.append(f"{row_label:<8} | " + " | ".join(row_outputs))

        return output_lines

    def _build_kmap_groups(self, implicants, form, variables, terms):
        if not terms:
            return [f"Constant function for {form}: no grouping needed."]

        if len(implicants) == 1 and set(implicants[0]["terms"]) == set(range(1 << len(variables))):
            return [f"Group 1: all cells -> {self._pattern_to_expression(implicants[0]['pattern'], variables, form)}"]

        groups = []
        for group_number, implicant in enumerate(implicants, start=1):
            cell_list = ", ".join(str(term) for term in sorted(implicant["terms"]))
            group_expression = self._pattern_to_expression(implicant["pattern"], variables, form)
            groups.append(f"Group {group_number}: cells [{cell_list}] -> {group_expression}")

        return groups

    def _pattern_to_expression(self, pattern, variables, form):
        if form == "SOP":
            pieces = []
            for index, bit in enumerate(pattern):
                if bit == "1":
                    pieces.append(variables[index])
                elif bit == "0":
                    pieces.append(f"{variables[index]}'")
            return "".join(pieces) if pieces else "1"

        pieces = []
        for index, bit in enumerate(pattern):
            if bit == "1":
                pieces.append(f"{variables[index]}'")
            elif bit == "0":
                pieces.append(variables[index])
        return "(" + " + ".join(pieces) + ")" if pieces else "(0)"

    def _print_truth_table(self, num_variables, truth_table):
        variables = self.variable_names[:num_variables]
        header = " | ".join(variables) + " | F"
        print("\nTruth Table")
        print(header)
        print("-" * len(header))

        for index in range(1 << num_variables):
            bits = format(index, f"0{num_variables}b")
            print(" | ".join(bits) + f" | {truth_table[bits]}")

    def _print_results(self, output_data):
        label = "Minterm list" if output_data["form"] == "SOP" else "Maxterm list"

        print(f"\nCanonical {output_data['form']} Equation")
        print(output_data["canonical_expression"])

        print(f"\n{label}")
        print(output_data["term_list"])

        print("\nK-Map")
        for line in output_data["kmap"]:
            print(line)

        print("\nK-Map Grouping")
        for line in output_data["kmap_groups"]:
            print(line)

        print("\nSimplified Boolean Expression")
        print(output_data["simplified_expression"])

        print("\nValidation Result")
        print(output_data["validation_result"])


processor = Processor()
processor.run()
