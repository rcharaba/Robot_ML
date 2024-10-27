import pandas as pd

def load_data(file_path):
    return pd.read_csv(file_path)

def group_test_cases(testcase_data):
    grouped = testcase_data.groupby(['rf_suite_name', 'rf_name']).agg(
        total_runs=pd.NamedAgg(column='build_number', aggfunc='count'),
        total_passes=pd.NamedAgg(column='rf_passed', aggfunc='sum'),
        total_failures=pd.NamedAgg(column='rf_failed', aggfunc='sum')
    ).reset_index()
    return grouped

def calculate_pass_fail_rates(grouped_data):
    grouped_data['pass_rate'] = grouped_data['total_passes'] / grouped_data['total_runs']
    grouped_data['fail_rate'] = grouped_data['total_failures'] / grouped_data['total_runs']
    return grouped_data

# Filter out tests that are always passing or always failing for further analysis
def filter_informative_tests(grouped_data):
    # Retain only tests with pass rates between 0% and 100%
    informative = grouped_data[(grouped_data['pass_rate'] > 0) & (grouped_data['pass_rate'] < 1)].copy()
    return informative

# Calculate a weighted score for each test case based on its variability and failure rate
def calculate_weighted_scores(informative_tests):
    informative_tests['variability'] = abs(0.5 - informative_tests['pass_rate'])
    # Create a weighted score: 70% weight to failure rate and 30% weight to variability
    informative_tests['weighted_score'] = informative_tests['fail_rate'] * 0.7 + informative_tests['variability'] * 0.3
    return informative_tests

def break_ties(group):
    """
    Break ties by prioritizing:
    1. The test case with the most runs (total_runs).
    2. If still tied, pick a random test case.
    """
    max_runs = group['total_runs'].max()
    tied_cases = group[group['total_runs'] == max_runs]

    # If there are multiple tied cases, randomly select one
    if len(tied_cases) > 1:
        return tied_cases.sample(n=1).iloc[0]
    else:
        return tied_cases.iloc[0]

# Select relevant test cases for each test suite based on a score threshold or a fixed number of tests
def select_optimized_tests(informative_tests, min_weighted_score=0.2, max_tests_per_suite=1):
    optimized_tests = []

    # Sort tests by suite and by their weighted score
    sorted_tests = informative_tests.sort_values(by=['rf_suite_name', 'weighted_score'], ascending=False)

    # For each test suite, pick the most relevant test cases
    for suite, group in sorted_tests.groupby('rf_suite_name'):
        # Filter by minimum weighted score if provided
        if min_weighted_score is not None:
            group = group[group['weighted_score'] >= min_weighted_score]

        # Limit the number of tests per suite if max_tests_per_suite is provided
        if max_tests_per_suite is not None:
            group = group.head(max_tests_per_suite)

        optimized_tests.extend(group.to_dict(orient='records'))

    return pd.DataFrame(optimized_tests)

def save_optimized_tests(optimized_tests_df, output_file):
    optimized_tests_df.to_csv(output_file, index=False)

def log_and_save_filtered_tests(grouped_data, output_file_filtered):
    total_test_cases = grouped_data['rf_name'].nunique()
    print(f"Total number of unique test cases: {total_test_cases}")

    # Filter out tests with pass rates of 100% or 0%
    filtered_tests = grouped_data[(grouped_data['pass_rate'] == 1) | (grouped_data['pass_rate'] == 0)]
    filtered_test_count = filtered_tests['rf_name'].nunique()

    # Save the filtered test cases to a CSV file
    filtered_tests.to_csv(output_file_filtered, index=False)

    print(f"Number of tests with 100% or 0% pass rate: {filtered_test_count}")
    print(f"Filtered test cases saved to {output_file_filtered}")

    return total_test_cases, filtered_test_count

# Reduction statistics
def calculate_reduction_stats(total_test_cases, optimized_tests_df):
    reduced_test_count = optimized_tests_df['rf_name'].nunique()
    reduction_percentage = ((total_test_cases - reduced_test_count) / total_test_cases) * 100

    print(f"Original number of test cases: {total_test_cases}")
    print(f"Reduced number of test cases: {reduced_test_count}")
    print(f"Reduction percentage: {reduction_percentage:.2f}%")


if __name__ == "__main__":
    input_file = 'testcase_data.csv'
    output_file_optimized = 'optimized_test_suite.csv'
    output_file_filtered = 'filtered_test_cases.csv'

    # Step 1: Load the test case data
    testcase_data = load_data(input_file)

    # Step 2: Group test cases and calculate pass/fail rates
    grouped_data = group_test_cases(testcase_data)
    grouped_data = calculate_pass_fail_rates(grouped_data)

    # Step 3: Log statistics and save filtered test cases for future analyses
    total_test_cases, filtered_test_count = log_and_save_filtered_tests(grouped_data, output_file_filtered)

    # Step 4: Filter informative tests and calculate their weighted scores
    informative_tests = filter_informative_tests(grouped_data)
    informative_tests = calculate_weighted_scores(informative_tests)

    # Step 5: Select the optimized test cases
    optimized_tests_df = select_optimized_tests(informative_tests)

    # Step 6: Save the optimized test suite
    save_optimized_tests(optimized_tests_df, output_file_optimized)

    # Step 7: Calculate and log the reduction in the number of test cases
    calculate_reduction_stats(total_test_cases, optimized_tests_df)

    # Log sample
    print(optimized_tests_df[['rf_suite_name', 'rf_name', 'total_runs', 'pass_rate', 'fail_rate', 'weighted_score']].head())
