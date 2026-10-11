"""Load Izdebski et al. 2022 Supplementary Data 2 into a tidy table."""
import openpyxl, pandas as pd
def load(path='izdebski2022_supp_data.xlsx'):
    ws = openpyxl.load_workbook(path, read_only=True).worksheets[1]
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[1]; df = pd.DataFrame(rows[2:], columns=hdr)
    df = df[df['Acronym'].notna()].copy()
    for c in ['Year', 'fast_succ', 'slow_succ', 'herding', 'cereals', 'fast_succ_new', 'slow_succ_new', 'Longitude', 'Latitude']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df = df.rename(columns={'Acronym': 'site', 'region_2': 'region'})
    return df
if __name__ == '__main__':
    d = load(); print(d.shape); print(d.head()); print(d.region.value_counts().sort_index())
    print('NA cereals:', d.cereals.isna().sum(), 'sites:', d.site.nunique())
