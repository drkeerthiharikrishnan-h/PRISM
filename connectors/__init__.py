from .pubmed import fetch as pubmed_fetch
from .chembl import fetch as chembl_fetch
from .pdb import fetch as pdb_fetch
from .uniprot import fetch as uniprot_fetch
from .pubchem import fetch as pubchem_fetch
from .clinvar import fetch as clinvar_fetch
from .reactome import fetch as reactome_fetch
from .alphafold import fetch as alphafold_fetch

REGISTRY = {
    "pubmed": pubmed_fetch,
    "chembl": chembl_fetch,
    "pdb": pdb_fetch,
    "uniprot": uniprot_fetch,
    "pubchem": pubchem_fetch,
    "clinvar": clinvar_fetch,
    "reactome": reactome_fetch,
    "alphafold": alphafold_fetch,
}
