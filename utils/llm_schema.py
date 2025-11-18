# Pydantic schema for LLM ↔ KG handoff (natural language → structured facts)
from env.modules import *
from data.mint_entities import df

class RowOut(BaseModel):
    # Human-readable material label (e.g., formula); becomes rdfs:label on EX.Material
    material: str

    # Columns we actually model in this project
    formula: Optional[str] = None                 # -> ex:hasFormula
    material_id: Optional[str] = None             # -> ex:hasExternalId
    crystal_system: Optional[str] = None          # -> ex:hasCrystalSystem
    is_centrosymmetric: Optional[bool] = None     # -> ex:hasCentrosymmetric

    # Numeric property (kept), no synthesis/lattice here
    band_gap_eV: Optional[float] = Field(default=None, ge=0)  # -> ex:hasBandGap (eV)
    
allowed_crystal_systems = sorted(set(str(x).strip() for x in df['crystal_system'].dropna()))
allowed_centrosym       = sorted(set(bool(x) for x in df['is_centrosymmetric'].dropna()))

## aliases for my old schema:
# allowed_structs = allowed_crystal_systems  
# allowed_methods = []    
                   
print("crystal_systems:", allowed_crystal_systems)
print("centrosymmetric values:", allowed_centrosym)