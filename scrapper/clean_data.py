import pandas as pd
df = pd.read_excel("data/jobyaari_jobs.xlsx")
print("Original shape:", df.shape)
print(df.head())
columns_except_category = [col for col in df.columns if col != 'category']
df = df.dropna(axis=0, how='all', subset=columns_except_category)
df = df.fillna('Not Disclosed')
df = df.reset_index(drop=True)
df.to_excel("data/jobyaari_jobs_cleaned.xlsx", index=False)
print("Cleaned shape:", df.shape)
print("Sample data after cleaning:")
print(df.head())
