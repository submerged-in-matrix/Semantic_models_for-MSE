from env.modules import *
from llm.normalize import normalize_row_with_ollama
from llm.ingest_from_txt import ingest_normalized_row
from llm.llm_def import _fetch_url_text
from ontology.core import *


def batch_ingest_urls(urls, start_idx: int = 1_000_000, text_preview_chars: int = 320):
    successes, rejects = [], []

    for k, url in enumerate(urls, start=0):
        try:
            nr = normalize_row_with_ollama({"url": url})   # STRICT: may raise ValueError
            m  = ingest_normalized_row(nr, idx=start_idx+k,
                                       source_label="web_import", source_id=url)
            # ingest_normalized_row now auto-tags metadata
            successes.append({
                "url": url,
                "material": nr.material,
                "formula": nr.formula,
                "material_id": nr.material_id,
                "crystal_system": nr.crystal_system,
                "is_centrosymmetric": nr.is_centrosymmetric,
                "band_gap_eV": nr.band_gap_eV,
            })
        except ValueError:
            # Not informative enough → show a short preview
            try:
                preview = shorten(_fetch_url_text(url, max_chars=4000), width=text_preview_chars, placeholder=" …")
            except Exception as fe:
                preview = f"[failed to fetch text: {fe}]"
            rejects.append({
                "url": url,
                "reason": "Text not informative enough to add in KG",
                "text_preview": preview,
            })
        except Exception as e:
            rejects.append({
                "url": url,
                "reason": f"Error: {e}",
                "text_preview": None,
            })

    df_ok  = pd.DataFrame(successes)
    df_bad = pd.DataFrame(rejects)
    print(f"Ingested: {len(df_ok)} | Rejected: {len(df_bad)} | Triples now: {len(g)}")
    if len(df_ok):
        display(df_ok.head(min(10, len(df_ok))))
    if len(df_bad):
        print("\nRejected entries (showing up to 10):")
        display(df_bad.head(min(10, len(df_bad))))
    return df_ok, df_bad