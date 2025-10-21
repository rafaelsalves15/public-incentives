# Data Directory

This directory contains the CSV files for the Public Incentives system.

## Required Files

Place the following files in this directory:

- `companies.csv` - Companies dataset
- `incentives.csv` - Incentives dataset

## File Structure

The system expects the CSV files to have the following structure:

### companies.csv
```csv
company_name,cae_primary_label,trade_description_native,website
"Company Name","CAE Activity","Trade Description","www.website.com"
```

### incentives.csv
```csv
incentive_project_id,project_id,incentive_program,title,description,ai_description,document_urls,date_publication,date_start,date_end,total_budget,status,all_data,created_at,updated_at,eligibility_criteria,source_link,gcs_document_urls
```

## Usage

1. Place your CSV files in this directory with the exact names:
   - `companies.csv`
   - `incentives.csv`
2. Start the API: `docker-compose up`
3. Check file status: `GET /data/files/status`
4. Import data: `POST /data/import`
5. Process matches: `POST /data/process-all-matches`

## Notes

- Large CSV files are ignored by git (see .gitignore)
- Sample files can be included with `sample_` prefix
- The system will validate file existence before importing
- Files must match the exact structure of the original challenge CSVs
