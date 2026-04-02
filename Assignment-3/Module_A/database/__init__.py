import os

# include the contents of the database package in Assignment-2
assn2_db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../Assignment-2/Module_A/database"))
if os.path.exists(assn2_db_path) and assn2_db_path not in __path__:
    __path__.append(assn2_db_path)

# idk but need to do it twice or it fails.
assn2_db_path2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../Assignment-2/Module_A/database"))
if os.path.exists(assn2_db_path2) and assn2_db_path2 not in __path__:
    __path__.append(assn2_db_path2)
