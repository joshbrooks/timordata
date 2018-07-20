# MySQL primary key -> PostgresQL primary key
import pickle


class Mapping:
    orgtype = {
        1: {"code": "INGO", "orgtype": "International NGO"},
        2: {"code": "CBO", "orgtype": "Community Based Organization"},
        3: {"code": "LNGO", "orgtype": "Local NGO"},
        4: {"code": "BI", "orgtype": "Bilateral Agency"},
        5: {"code": "AC", "orgtype": "Academic / Research Agency"},
        6: {"code": "None", "orgtype": "Unknown type"},
        7: {"code": "UN", "orgtype": "United Nations agency"},
    }
    projectstatus = {
        1: {"code": "A", "description": "Active"},
        2: {"code": "C", "description": "Completed"},
        3: {"code": "X", "description": "Cancelled"},
        4: {"code": "U", "description": "Unknown"},
        5: {"code": "P", "description": "Planned"},
    }

    projectorganizationclass = {
        "P": {"code": "P", "description": "Primary"},
        "A": {"code": "A", "description": "Partner"},
        "F": {"code": "F", "description": "Funding"},
        "O": {"code": "O", "description": "Other"},
    }

    act = {
        1: {"path": "ACT.DLG", "name": "Dialogue"},
        2: {"path": "ACT.TRN", "name": "Training"},
        3: {"path": "ACT.CAP", "name": "Capacity Strengthening"},
        4: {"path": "ACT.ADV", "name": "Advocacy"},
        5: {"path": "ACT.RES", "name": "Research"},
        6: {"path": "ACT.SSV", "name": "Social Services"},
        7: {"path": "ACT.INF", "name": "Infrastructure and Rehabilitation"},
        8: {"path": "ACT.INC", "name": "Dialogue"},
        9: {"path": "ACT.MFC", "name": "Dialogue"},
        10: {"path": "ACT.DLG", "name": "Dialogue"},
        14: {"path": "ACT.GRA", "name": "Small Grants"},
        17: {"path": "ACT.PUB", "name": "Public Information"},
        18: {"path": "ACT.ADS", "name": "Advisory Support"},
        19: {"path": "ACT.NET", "name": "Networking"},
    }

    ben = {
        2: {"path": "BEN.YOU", "name": "Youth"},
        3: {"path": "BEN.COM", "name": "Community (general)"},
        4: {"path": "BEN.CHI", "name": "Children"},
        5: {"path": "BEN.WOM", "name": "Women"},
        7: {"path": "BEN.WID", "name": "Widows"},
        24: {"path": "BEN.ORG", "name": "Organizations"},
        26: {"path": "BEN.GOV", "name": "Government"},
        27: {"path": "BEN.PRO", "name": "Professionals"},
        28: {"path": "BEN.SUR", "name": "Survivors of Violence"},
        29: {"path": "BEN.IDP", "name": "IDPs"},
        30: {"path": "BEN.SCC", "name": "Suco councils"},
        31: {"path": "BEN.EXC", "name": "Ex-combatants"},
        32: {"path": "BEN.SPE", "name": "Special Needs"},
        33: {"path": "BEN.FAR", "name": "Farmers"},
        34: {"path": "BEN.HIV", "name": "People living with HIV/Aids"},
        35: {"path": "BEN.COU", "name": "Couples"},
    }
    inv = {
        1: {"name": "Education", "path": "INV.EDU"},
        2: {"name": "Agriculture and Food Security", "path": "INV.AGR"},
        3: {"name": "Dialogue", "path": "INV.DLG"},
        4: {"name": "Health", "path": "INV.HLT"},
        5: {"name": "Community Development", "path": "INV.CDV"},
        6: {"name": "Natural Resources Enviroment and Energy", "path": "INV.NAT"},
        7: {"name": "Infrastructure", "path": "INV.INF"},
        8: {"name": "Justice Human Rights and Protection", "path": "INV.JUS"},
        9: {"name": "Water and Sanitation", "path": "INV.WAT"},
        10: {"name": "Economic Development", "path": "INV.ECD"},
        11: {"name": "Conflict Prevention and Peace Strengthening", "path": "INV.CPP"},
        12: {"name": "Governance", "path": "INV.GOV"},
        13: {"name": "Media and Public Information", "path": "INV.MED"},
        14: {"name": "Gender Equality", "path": "INV.GEN"},
        15: {"name": "Coordination", "path": "INV.CRD"},
        16: {"name": "Fisheries", "path": "INV.FIS"},
        17: {"name": "Nutricion", "path": "INV.NUT"},
        18: {"name": "Disaster Risk Management", "path": "INV.DRM"},
        19: {"name": "HIV/Aids", "path": "INV.HIV"},
        20: {"name": "Food Aid", "path": "INV.FDA"},
        21: {"name": "Emergency Shelter", "path": "INV.SHL"},
        22: {"name": "Security", "path": "INV.SEC"},
    }

    # Pcodes: Key is old pcode, Value is new pcode
    pcodes = pickle.load(open("csv_translate.pickle"))
