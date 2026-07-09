from .pubmed import fetch as pubmed_fetch
from .chembl import fetch as chembl_fetch
from .pdb import fetch as pdb_fetch
from .uniprot import fetch as uniprot_fetch
from .pubchem import fetch as pubchem_fetch
from .clinvar import fetch as clinvar_fetch
from .reactome import fetch as reactome_fetch
from .alphafold import fetch as alphafold_fetch
from .interpro import fetch as interpro_fetch
from .string_ppi import fetch as string_ppi_fetch
from .opentargets import fetch as opentargets_fetch
from .gtex import fetch as gtex_fetch
from .admet import fetch as admet_fetch
from .proteinatlas import fetch as proteinatlas_fetch

REGISTRY = {
    "pubmed": pubmed_fetch,
    "chembl": chembl_fetch,
    "pdb": pdb_fetch,
    "uniprot": uniprot_fetch,
    "pubchem": pubchem_fetch,
    "clinvar": clinvar_fetch,
    "reactome": reactome_fetch,
    "alphafold": alphafold_fetch,
    "interpro": interpro_fetch,
    "string_ppi": string_ppi_fetch,
    "opentargets": opentargets_fetch,
    "gtex": gtex_fetch,
    "admet": admet_fetch,
    "proteinatlas": proteinatlas_fetch,
}
