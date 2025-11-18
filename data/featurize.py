from env.modules import *
from utils.regex_str import parse_pretty_structure, INPUT_XLSX, OUTPUT_CSV

# -------- Load Excel ----------
df = pd.read_excel(INPUT_XLSX)

# Choose/confirm structure column 
struct_col = "structure" if "structure" in df.columns else None
if struct_col is None:
    # try a best-guess search for a column that contains the pretty summary
    candidates = [c for c in df.columns if df[c].astype(str).str.contains(r"Full Formula|Reduced Formula|Sites \(", regex=True, na=False).any()]
    struct_col = candidates[0] if candidates else None

if struct_col is None:
    raise ValueError(f"Could not find the structure column. Available columns: {list(df.columns)}")

# -------- Parse structures --------
parsed = df[struct_col].apply(parse_pretty_structure)

parsed_ok = parsed.apply(lambda x: isinstance(x, Structure))
print(f"Parsed {parsed_ok.sum()} / {len(parsed)} structures ({100*parsed_ok.mean():.1f}%).")

if parsed_ok.sum() == 0:
    raise RuntimeError("Parser could not reconstruct any structures from the pretty string format. "
                       "Please share one exact cell (as plain text) or consider storing CIF/JSON for structures.")

# Replace column with parsed Structure objects
df[struct_col] = parsed

# -------- Featurize (two features only) --------
gsf = GlobalSymmetryFeatures()
labels = gsf.feature_labels()  # ['spacegroup_num','crystal_system','crystal_system_int','is_centrosymmetric','n_symmetry_ops']

records = []
for s in df[struct_col]:
    if isinstance(s, Structure):
        try:
            vals = gsf.featurize(s)
            rec = dict(zip(labels, vals))
        except Exception:
            rec = {lbl: np.nan for lbl in labels}
    else:
        rec = {lbl: np.nan for lbl in labels}
    records.append(rec)

feat_df = pd.DataFrame(records)
out_df = pd.concat([df.reset_index(drop=True),
                    feat_df[["crystal_system", "is_centrosymmetric"]].reset_index(drop=True)], axis=1)

# -------- Save --------
out_df.to_csv(OUTPUT_CSV, index=False)
print(f"Saved: {OUTPUT_CSV}")
print(out_df[["crystal_system", "is_centrosymmetric"]].isna().mean())
out_df.head()