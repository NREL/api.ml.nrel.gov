import logging
import os
import urllib.parse
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ysi_api.fragdecomp.chemical_conversions import canonicalize_smiles
from ysi_api.fragdecomp.fragment_decomposition import (
    FragmentError,
    draw_fragment,
    draw_mol_svg,
)
from ysi_api.prediction import predict, return_fragment_matches

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def quote(x):
    return urllib.parse.quote(x, safe="")


# FastAPI changes below
class Prediction(BaseModel):
    mean: Optional[float] = None
    std: Optional[float] = None
    outlier: Optional[bool] = None
    exp_mean: Optional[float] = None
    exp_std: Optional[float] = None
    exp_name: Optional[str] = None
    status: str


class Result(BaseModel):
    mean: Optional[float] = None
    std: Optional[float] = None
    outlier: Optional[bool] = None
    exp_mean: Optional[float] = None
    exp_std: Optional[float] = None
    exp_name: Optional[str] = None
    status: str
    mol_svg: Optional[str] = None
    svg: Optional[str] = None
    frag_df: Optional[dict] = None
    frag_missing_df: Optional[dict] = None
    named_smiles: Optional[str] = None


class Frag(BaseModel):
    frag_str: Optional[str] = None
    frag_svg: Optional[str] = None
    fragrow: Optional[dict] = None
    matches: Optional[dict] = None
    status: str


class Message(BaseModel):
    message: str


description = """This tool predicts the Yield Sooting Index of a compound
as a function of its carbon types. To use, enter a SMILES string above (or
use the drawing tool) and press submit. Experimental measurements, when
available, are also displayed."""
tags_metadata = [
    {
        "name": "predict",
        "description": "Group-contribution predictions of Yield Sooting Index (YSI)",
    },
]

app = FastAPI(
    title="YSI Estimator",
    description=description,
    version="1.0",
    # terms_of_service="http://example.com/terms/",
    contact={
        "name": "Peter St. John",
        "url": "https://www.nrel.gov/research/peter-stjohn.html",
    },
    # license_info={
    #     "name": "TBD",
    #     "url": "TBD",
    # },
    openapi_tags=tags_metadata,
)
smiles_path = Path(..., title="Enter a SMILES string", example="CC1=CC(=CC(=C1)O)C")


@app.get("/canonicalize/{smiles:path}", responses={400: {"model": Message}})
async def canonicalize(smiles: str):
    try:
        can_smiles = canonicalize_smiles(smiles)
        if can_smiles is None:
            raise Exception()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid smiles: %s" % smiles)
    return can_smiles


@app.get("/predict/{smiles:path}", response_model=Prediction, tags=["predict"])
async def api_predict(smiles: str = Depends(canonicalize)):
    try:
        mean, std, outlier, frag_df, exp_mean, exp_std, exp_name = predict(smiles)
    except FragmentError:
        # Most likely a poorly-formed SMILES string.
        errmsg = (
            'Error: "{}" SMILES string invalid. Please enter a valid SMILES '
            "without quotes.".format(smiles)
        )
        raise HTTPException(status_code=400, detail=errmsg)
    except Exception as ex:
        # Most likely a poorly-formed SMILES string.
        if "c" not in smiles.lower():
            errmsg = 'Error: Input SMILES "{}" must contain a carbon ' "atom.".format(
                smiles
            )
            raise HTTPException(status_code=400, detail=errmsg)
        errmsg = "Error: Exception occurred with input " "{0}: {1}".format(smiles, ex)
        raise HTTPException(status_code=400, detail=errmsg)
    return {
        "mean": mean,
        "std": std,
        "outlier": outlier,
        "exp_mean": exp_mean,
        "exp_std": exp_std,
        "exp_name": exp_name,
        "status": "ok",
    }


@app.get("/predict", response_model=Prediction, tags=["predict"])
async def api_predict_with_query(smiles: str):
    results = await api_predict(smiles)
    return results


@app.get("/result/{smiles:path}", response_model=Result, tags=["result"])
async def api_result(
    smiles: str = Depends(canonicalize),
):
    try:
        # Here's the real prediction step. We calculated the predicted mean +/-
        # std, draw the whole molecule, and return a dataframe of the component
        # fragments.
        mean, std, outlier, frag_df, exp_mean, exp_std, exp_name = predict(smiles)
        mol_svg = draw_mol_svg(
            smiles,
            figsize=(150, 150),
            color_dict=dict(zip(frag_df.index, frag_df.color)),
        )
        mean = round(mean, 1)
        std = round(std, 1)
        frag_df["frag_link"] = frag_df.index
        frag_df["frag_link"] = frag_df["frag_link"].apply(quote)
        if exp_name:
            smiles += " ({})".format(exp_name)
        return Result(
            mol_svg=mol_svg,
            mean=mean,
            std=std,
            frag_df=frag_df[frag_df["train_count"] > 0].to_dict(),
            outlier=outlier,
            exp_mean=exp_mean,
            exp_std=exp_std,
            frag_missing_df=frag_df[frag_df["train_count"] == 0].to_dict(),
            named_smiles=smiles,
            status="ok",
        )
    except FragmentError:
        # Most likely a poorly-formed SMILES string.
        errmsg = (
            'Error: "{}" SMILES string invalid. Please enter a valid SMILES '
            "without quotes.".format(smiles)
        )
        raise HTTPException(status_code=400, detail=errmsg)
    except Exception as ex:
        # Most likely a poorly-formed SMILES string.
        if "c" not in smiles.lower():
            errmsg = 'Error: Input SMILES "{}" must contain a carbon ' "atom.".format(
                smiles
            )
            raise HTTPException(status_code=400, detail=errmsg)
        errmsg = "Error: Exception occurred with input " "{0}: {1}".format(smiles, ex)
        raise HTTPException(status_code=400, detail=errmsg)


@app.get("/frag/{frag_str:path}", response_model=Frag, tags=["frag"])
async def api_frag(
    frag_str: str,
):
    color = (0.9677975592919913, 0.44127456009157356, 0.5358103155058701)
    try:
        frag_svg = draw_fragment(frag_str, color)
        fragment_row, matches = return_fragment_matches(frag_str)
    except KeyError:
        errmsg = 'Fragment "{}" not found'.format(frag_str)
        raise HTTPException(status_code=400, detail=errmsg)
    except AttributeError as ae:
        errmsg = "AttributeError: " + str(ae)
        raise HTTPException(status_code=400, detail=errmsg)
    matches["smiles_link"] = matches.SMILES.apply(quote)
    # Some of the Type and CAS fields return NAN, which breaks json
    md = matches.fillna("").to_dict()
    return Frag(
        frag_str=frag_str,
        frag_svg=frag_svg,
        fragrow=fragment_row.to_dict(),
        matches=md,
        status="ok",
    )


script_dir = os.path.dirname(__file__)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
