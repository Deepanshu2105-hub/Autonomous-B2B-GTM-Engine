from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# Map V1 CSV column names to the V2 schema.
# Replace the values on the right with the exact column names in your V1 file.
COLUMN_MAPPING = {
 "Company Name": "Company",
 "Website URL": "Website",
 "Contact Persona": "Persona",
 "Email": "Persona Email",
}

V2_COLUMNS = ["Company", "Website", "Persona", "Persona Email"]

class LeadMigration:
 """Validate, clean, and export leads from a V1 tracker CSV."""

 def __init__(
 self,
 input_path: Path,
 output_path: Path,
 column_mapping: dict[str, str] = COLUMN_MAPPING,
 ) -> None:
 self.input_path = input_path
 self.output_path = output_path
 self.column_mapping = column_mapping

 self.duplicates_removed = 0
 self.rows_missing_email = 0

 def run(self) -> pd.DataFrame:
 """Load, transform, export, and report on the migration."""
 data = self._read_csv()
 data = self._standardize_columns(data)
 data = self._clean_values(data)
 data = self._remove_duplicate_companies(data)
 data = self._remove_missing_emails(data)
 data = data[V2_COLUMNS]

 self._export_csv(data)
 self._print_summary(len(data))

 return data

 def _read_csv(self) -> pd.DataFrame:
 """Read the V1 CSV and normalize header whitespace."""
 if not self.input_path.is_file():
 raise FileNotFoundError(f"Input CSV not found: {self.input_path}")

 data = pd.read_csv(self.input_path)
 data.columns = data.columns.astype(str).str.strip()

 missing = set(self.column_mapping) - set(data.columns)
 if missing:
 expected = ", ".join(sorted(missing))
 raise ValueError(f"V1 CSV is missing required source columns: {expected}")

 return data

 def _standardize_columns(self, data: pd.DataFrame) -> pd.DataFrame:
 """Rename V1 fields to the V2 schema."""
 return data.rename(columns=self.column_mapping)

 @staticmethod
 def _clean_values(data: pd.DataFrame) -> pd.DataFrame:
 """Trim text fields and normalize blank cells to missing values."""
 cleaned = data.copy()

 for column in V2_COLUMNS:
 cleaned[column] = cleaned[column].astype("string").str.strip()
 cleaned[column] = cleaned[column].replace("", pd.NA)

 return cleaned

 def _remove_duplicate_companies(self, data: pd.DataFrame) -> pd.DataFrame:
 """Keep the first row for each company, ignoring case and whitespace."""
 cleaned = data.copy()
 company_key = cleaned["Company"].str.casefold()

 before = len(cleaned)
 cleaned = cleaned.loc[
 company_key.notna() & ~company_key.duplicated(keep="first")
 ].copy()
 self.duplicates_removed = before - len(cleaned)

 return cleaned

 def _remove_missing_emails(self, data: pd.DataFrame) -> pd.DataFrame:
 """Remove rows with no email address."""
 before = len(data)
 cleaned = data.dropna(subset=["Persona Email"]).copy()
 self.rows_missing_email = before - len(cleaned)

 return cleaned

 def _export_csv(self, data: pd.DataFrame) -> None:
 """Write V2-ready data using the exact V2 column order."""
 self.output_path.parent.mkdir(parents=True, exist_ok=True)
 data.to_csv(self.output_path, index=False)

 def _print_summary(self, clean_lead_count: int) -> None:
 """Print a concise migration report to the terminal."""
 print("V1 → V2 migration complete")
 print(f"Duplicate companies removed: {self.duplicates_removed:,}")
 print(f"Rows dropped for missing email: {self.rows_missing_email:,}")
 print(f"Clean leads ready for V2: {clean_lead_count:,}")
 print(f"Output file: {self.output_path}")

def main() -> None:
 parser = argparse.ArgumentParser(
 description="Clean and migrate a V1 GTM tracker CSV to the V2 lead schema."
 )
 parser.add_argument(
 "input_csv",
 type=Path,
 help="Path to the older V1 tracker CSV.",
 )
 parser.add_argument(
 "--output",
 type=Path,
 default=Path("v2_ready_leads.csv"),
 help="Output path (default: v2_ready_leads.csv).",
 )
 args = parser.parse_args()

 migration = LeadMigration(args.input_csv, args.output)
 migration.run()

if __name__ == "__main__":
 main()
