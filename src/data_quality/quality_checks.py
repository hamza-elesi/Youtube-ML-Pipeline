# File: src/data_quality/quality_checks.py
import great_expectations as ge
import pandas as pd

def run_data_quality_checks(df):
    # Convert the dictionary to a DataFrame if it's not already
    if isinstance(df, dict):
        df = pd.DataFrame(df)
    
    # Convert the DataFrame to a Great Expectations DataFrame
    ge_df = ge.from_pandas(df)

    # Define expectations
    ge_df.expect_column_to_exist('textDisplay')
    ge_df.expect_column_values_to_not_be_null('textDisplay')
    ge_df.expect_column_to_exist('likeCount')
    ge_df.expect_column_values_to_be_of_type('likeCount', 'int64')
    ge_df.expect_column_values_to_be_between('likeCount', min_value=0, max_value=1000000)

    # Validate the expectations
    results = ge_df.validate()

    # Check if all expectations were met
    if not results.success:
        failed_expectations = [result for result in results.results if not result.success]
        raise ValueError(f"Data quality check failed. Failed expectations: {failed_expectations}")

    return True