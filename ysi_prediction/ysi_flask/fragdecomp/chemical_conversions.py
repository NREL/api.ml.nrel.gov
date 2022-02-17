from rdkit.Chem import MolFromSmiles, MolToSmiles


def canonicalize_smiles(smiles: str, isomeric=True) -> str:
    try:
        mol = MolFromSmiles(smiles)
        return MolToSmiles(mol, isomericSmiles=isomeric)
    except Exception:
        pass
