import json


def load_reports(filepath="test/e3/job/reports.json"):
    """Load reports data from a JSON file."""
    with open(filepath) as f:
        return json.load(f)


def split_reports(data, tail_size=3):
    """Split data into two parts: data[:-tail_size] and data[-tail_size:]."""
    return data[:-tail_size], data[-tail_size:]


def sum_report_keys(reports):
    """
    Compute the sum of the following keys in each report:
      - round_index_creation_time
      - round_query_execution_time
      - round_config_reset_time
      - round_reconfiguration_time
    Returns a dictionary mapping the key to its total sum.
    """
    keys = [
        "round_index_creation_time",
        "round_query_execution_time",
        "round_config_reset_time",
        "round_reconfiguration_time",
    ]
    totals = {key: sum(item.get(key, 0) for item in reports) for key in keys}
    return totals


def print_totals(totals, title="Totals"):
    """
    Print the total values and their percentage share of the sum.
    """
    total_sum = sum(totals.values())
    print(f"{title} (Total Sum: {total_sum:.2f}):")
    for key, value in totals.items():
        # Avoid division by zero if total_sum is zero.
        share = (value / total_sum) if total_sum else 0
        print(f"  {key}: {value:.2f} ({share:.2%})")
    print()


def main():
    data = load_reports()

    # Split the data: first part (lambda_tune) and last 3 items (continue_loop)
    lambda_tune, continue_loop = split_reports(data)

    # Print totals for lambda_tune part
    lambda_totals = sum_report_keys(lambda_tune)
    print_totals(lambda_totals, title="Lambda Tune Totals")

    # Print totals for continue_loop part
    continue_totals = sum_report_keys(continue_loop)
    print_totals(continue_totals, title="Continue Loop Totals")


if __name__ == "__main__":
    main()
