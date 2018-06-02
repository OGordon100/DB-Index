import re
import numpy as np
from DBFinder import DBCalculator
import json

# Open DB database
with open('Database.json', 'r') as fp:
        Database = json.load(fp)

