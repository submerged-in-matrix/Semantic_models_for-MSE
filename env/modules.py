import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import json, ast
import requests
from datetime import datetime, timezone
from IPython.display import display, HTML
from pyparsing import ParseException as PyParsingParseException
import gzip

import openpyxl
from graphviz import Digraph

import re
from pymatgen.core import Structure, Lattice
from matminer.featurizers.structure import GlobalSymmetryFeatures

from pydantic import BaseModel, Field, ValidationError
from typing import Any, Iterable, Optional
import  ollama
from rdflib import Graph, Namespace, RDF, RDFS, XSD, URIRef, Literal, BNode
from bs4 import BeautifulSoup
import hashlib
from textwrap import shorten

from pyvis.network import Network