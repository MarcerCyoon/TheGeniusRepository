import json
import re

TEST_SIZE = None

# abbreviation to full name
HEADER_TO_ORG_NAME = {
    'TG2': 'The Genius: Rule Breaker',
    'SMOG1': 'The Genius Forum Game',
    'TSG': 'The Subreddit Game',
    'Y&amp;Y': 'Yin and Yang',
    'SMOG2': 'Genius Game - Grand Final',
    'TG: Social': 'The Genius Social',
    'GG3': 'Genius Game 3',
    'GO:TR': 'Genius Online: Tabula Rasa',
    'GG3.3': 'Genius Game 3.3',
    'GO: Deadly Influx': 'Genius Online: Deadly Influx',
    'Zero&#x27;s Gambit': 'Zero&#x27;s Gambit',
    'GO:B&amp;P': 'Genius Online: Business &amp; Pleasure',
    'Master of all Trades': 'Master Of All Trades',
    'Master Of All Trades': 'Master Of All Trades',
    'EMG': 'EpicMafia Genius',
    'TG: Deception': 'The Genius: Deception',
    'DMC': 'DM Colosseum',
    'The Choice is Yours': 'The Choice is Yours',
    'Zero&#x27;s Gauntlet': 'Zero&#x27;s Gauntlet',
    'EMG2': 'EpicMafia Genius 2',
    'CHGG1': 'Community Hosted Genius Game',
    'Genius Invitational': 'Genius Invitational',
    'Code of Conduct': 'The Genius: Code of Conduct',
    'Bang-A-Rang I': 'Bang-A-Rang The Genius 1',
    'Genius Game 4': 'Genius Game 4',
    'GG4': 'Genius Game 4',
    'Kill Sam': 'Kill Sam',
    'House of Larks': 'The Genius: House of Larks',
    'GO:AS': 'Genius Online: All Stars',
    'Exordium': 'Exordium',
    'AGDQ': 'Andy&#x27;s Genius Done Quick',
    'DMC2': 'DM Colosseum 2',
    'Squeaky Genius': 'Squeaky Genius: Legends Untold',
    'Blooming Genius': 'Blooming Genius: The Elder Tree',
    'Blooming Genius: The Elder Tree': 'Blooming Genius: The Elder Tree',
    'Code Breakers': 'The Genius: Code Breakers',
    'CHGG2': 'Community Hosted Genius Game 2',
    'Puzzler': 'The Genius Puzzler',
    'Mainly By Design': 'Mainly By Design',
    'DOW: The Genius': 'DOW: The Genius',
    'Tempo Up': 'The Genius: Tempo Up',
    'TG: Code Red': 'The Genius: Code Red',
    'SMG1': 'Shardren&#x27;s Minecraft Genius: How to Play',
    'CHGG3': 'Community Hosted Genius Game 3',
    'First Encounter': 'The Genius: First Encounter',
    'H&amp;H': 'The Genius: Heaven and Hell',
    'HnH': 'The Genius: Heaven and Hell',
    'Bidders&#x27; Paradise': 'Bidders&#x27; Paradise',
    'Gambit Game': 'Gambit Game: First Move',
    'TSA': 'tdhe smartass',
    'SMG2': 'Shardren&#x27;s Minecraft Genius: How to Survive',
    'VoaT': 'The Genius: Variations on a Theme',
    'The Genius: PnP': 'The Genius: PnP',
    'PnP': 'The Genius: PnP',
    'Deadly By Design': 'Deadly By Design',
    'Simulacrum': 'The Simulacrum',
    'GGG': 'Gold&#x27;s Genius Game',
    'Zero&#x27;s Guardians': 'Zero&#x27;s Guardians',
    'Zero&#x27;s Guardians: Nilnought': 'Zero&#x27;s Guardians',
    'Zero&#x27;s Guardians: Nullnada': 'Zero&#x27;s Guardians',
    'Contractual Obligation': 'The Genius: Contractual Obligation',
    'EOW: The Genius': 'EOW: The Genius',
    'Champ The Champion': 'The Genius: Champ The Champion',
    'TG: Code Redone': 'The Genius: Code Redone',
    'SMG3': 'Shardren&#x27;s Minecraft Genius: How to Adapt',
    'Chopped': 'Chopped: An April Fool&#x27;s Design Competition',
    'Cosmic Banquet': 'The Genius: Cosmic Banquet',
    'Genius One': 'Genius One',
    'Simply Genius': 'Simply Genius',
    'Weekend Genius': 'Weekend Genius',
    'Genius Recharged': 'Genius Recharged'
}

ORG_NAME_TO_ID = {}

# generated from org_to_id.py
with open('ORG_DATA.json', 'r', encoding='utf-8') as file:
     ORG_NAME_TO_ID = json.load(file)

def create_test_data():
    with open("matches.json", "r") as file:
        matches = json.load(file)

    if TEST_SIZE is None:
        matches = matches
    else:
        matches = matches[:TEST_SIZE]

    with open("testdata.json", "w") as file:
        json.dump(matches, file, indent=4)

def create_new_match(old_match):
    new_match = {
        'id': old_match['id'],
        'name': old_match['name'],
        'designers': old_match['designers'],
        'summary': old_match['summary'],
        'see_also': old_match['see_also'],
        'awards': old_match['awards'],
        'match_type': old_match['match_type']
    }

    return new_match

def create_new_ruleset(match, rules, org, episode, tags, player_count):
    ruleset = {
        'match': match,
        'rules': rules,
        'ORG': org,
        'episode': episode,
        'tags': tags,
        'player_count': player_count,
    }

    return ruleset

def get_header(org, rules_headers):
    try:
        # use information in header to deduce which ORG it might be from.
        regex_data = [(re.search(r'\(([^\)]+)\)', header), header) for header in rules_headers]
        # default to the full header if the regex search failed, because in my research
        # the only case where there are no parentheses are the DMCs, in which case the
        # entire header is just the acronym itself
        extracted_org_acronyms = [data[0][0].replace("(", "").replace(")", "") if data[0] is not None else data[1] for data in regex_data]
        org_names = [ORG_NAME_TO_ID[HEADER_TO_ORG_NAME[header]] for header in extracted_org_acronyms]

        if org in org_names:
            return org_names.index(org)
        else:
            return None
    except KeyError:
        return -1

def get_episode(header):
    return header.split("(")[0].strip()

def get_org(header):
    regex = re.search(r'\(([^\)]+)\)', header)
    abbrev = regex[0].replace("(", "").replace(")", "") if regex is not None else header

    try:
        return ORG_NAME_TO_ID[HEADER_TO_ORG_NAME[abbrev]]
    except KeyError:
        return "-1"

if __name__ == "__main__":
    create_test_data()

    with open("testdata.json", "r") as file:
        old_matches = json.load(file)

    # create two different JSONs — a Match JSON and a Rulesets JSON
    matches = []
    rulesets = []
    variable_player_size = set()

    failed = 0
    missing = 0

    # variables to validate that we've converted all matches and rulesets in the repo.
    validate_matches = 0
    validate_rulesets = 0

    for old_match in old_matches:
        print(old_match['name'])

        new_match = create_new_match(old_match)

        # we remove the first indice, as every rules starts with $%^ and thus has an empty string at the start of the split.
        rules_split = old_match['rules'].split("$%^")[1:] 
        rules_headers = rules_split[::2] # even indices have headers
        rules_list = rules_split[1::2] # odd indices have actual rules text

        assert len(rules_headers) == len(rules_list)

        validate_matches += 1
        validate_rulesets += len(rules_headers)

        used_headers = []

        for org in old_match['ORGs'].split(','):
            index = get_header(org, rules_headers)

            if index == -1:
                print(f"A KeyError occurred: {rules_headers}. Terminating converting this match.")
                failed += 1
                break

            if old_match['max_players'] != "":
                variable_player_size.add(old_match['name'])

            if index is not None:
                used_headers.append(rules_headers[index])

                episode = get_episode(rules_headers[index])
                ruleset = create_new_ruleset(old_match['id'], rules_list[index], org, episode, old_match['tags'], old_match['min_players'])  

            else:
                ID_TO_ORG_NAME = {y: x for x, y in ORG_NAME_TO_ID.items()}
                print(f"Missing rules for {old_match['name']} for {ID_TO_ORG_NAME[org]}.")
                missing += 1

                episode = "TBD"
                ruleset = create_new_ruleset(old_match['id'], "-", org, episode, "", old_match['min_players'])
                
            rulesets.append(ruleset)

        if len(used_headers) != len(rules_headers):
            # There's some ruleset that hasn't been translated to the new format.
            # This usually happens because a game was played multiple times with
            # different rulesets in the same ORG (such as being both a DM and FM).
            # Let's translate the leftover rulesets so that they're not left behind.
            for header, rules in zip(rules_headers, rules_list):
                if not header in used_headers:
                    episode = get_episode(header)
                    org = get_org(header)

                    if org == "-1":
                        print(f"A KeyError occurred: {header}. Terminating converting this match.")

                    ruleset = create_new_ruleset(old_match['id'], rules, org, episode, old_match['tags'], old_match['min_players'])
                    rulesets.append(ruleset)
                
        matches.append(new_match)
        print()

    print(f"Matches in the Repo: {validate_matches} / Rulesets in the Repo: {validate_rulesets} / Missing Rulesets: {missing}")
    print(f"Converted Matches: {len(matches)} / Converted Rulesets: {len(rulesets)}")

    with open('NEW_MATCHES.json', 'w', encoding='utf-8') as file:
        json.dump(matches, file, indent=4)

    with open('NEW_RULESETS.json', 'w', encoding='utf-8') as file:
        json.dump(rulesets, file, indent=4)

    print("Failed conversions: " + str(failed) + "\n")

    print("The below Matches had a **variable player** count stored on the repo. This information is lost during conversion, thus it must be reconstructed manually.")
    print(variable_player_size)
