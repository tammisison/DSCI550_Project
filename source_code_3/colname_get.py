import os
import pandas as pd
from datetime import datetime

# Paths
input_path = os.path.join("..", "data_3", "final_haunted_analysis.tsv")
output_header_path = os.path.join("..", "data_3", "colheader.txt")

# Load TSV
df = pd.read_csv(input_path, sep='\t')

# Rename 'image' to 'image_path' and format as dict string
if "image" in df.columns:
    df = df.rename(columns={"image": "image_path"})
    df["image_path"] = df["image_path"].apply(
        lambda x: '{{"id": "{}"}}'.format(x) if pd.notnull(x) and not str(x).strip().startswith("{") else x
    )

# Rename 'caption_candidates' to 'caption_options'
if "caption_candidates" in df.columns:
    df = df.rename(columns={"caption_candidates": "caption_options"})

# Rename 'hp_date' to 'hp_day' and format to YYYY-MM-DD
if "hp_date" in df.columns:
    df = df.rename(columns={"hp_date": "hp_day"})

    # Format as just the date part (etllib.py will append T00:00:00.000Z)
    def to_solr_date(val):
        try:
            parsed = pd.to_datetime(val, errors='coerce')
            if pd.notnull(parsed):
                return parsed.strftime("%Y-%m-%d")
            return None
        except:
            return None

    df["hp_day"] = df["hp_day"].apply(to_solr_date)

# Save updated header
with open(output_header_path, 'w', encoding='utf-8') as f:
    for col in df.columns:
        f.write(col + '\n')

# Save TSV back (overwrite)
df.to_csv(input_path, sep='\t', index=False)

print(f"'image' → 'image_path' and patched.")
print(f"'caption_candidates' → 'caption_options'.")
print(f"'hp_date' → 'hp_day' and formatted to YYYY-MM-DD.")
print(f"Header saved to: {output_header_path}")
print(f"TSV overwritten at: {input_path}")
