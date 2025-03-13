import pandas as pd
from datetime import datetime
from dataframe_wrapper import DataFrameWrapper

# Simulate receiving a DataFrame that might not support dot notation for "datetime"
data = {
    "publishedAt": [datetime(2023, 1, 1, 12, 0), datetime(2023, 1, 2, 12, 0)],
    "headline": ["Headline 1", "Headline 2"],
    "content": ["Content 1", "Content 2"]
}
df = pd.DataFrame(data)

# Ensure there's a "datetime" column by renaming if needed
if 'datetime' not in df.columns:
    if 'publishedAt' in df.columns:
        df.rename(columns={'publishedAt': 'datetime'}, inplace=True)
    elif 'date' in df.columns:
        df.rename(columns={'date': 'datetime'}, inplace=True)
    else:
        df['datetime'] = datetime.now().isoformat()

# Wrap the DataFrame
wrapped_df = DataFrameWrapper(df)

# Now you can use dot notation:
print("Using dot notation:", wrapped_df.datetime)