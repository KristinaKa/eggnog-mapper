from collections import defaultdict
import json

def normalize_target_taxa(target_taxa):

    """
    Receives a list of taxa IDs and/or taxa names and returns a set of expanded taxids numbers
    """
    from ete3 import NCBITaxa
    ncbi = NCBITaxa()
    expanded_taxa = set()

    for taxon in target_taxa:
        taxid = ""
        try:
            taxid = int(taxon)
        except ValueError:
            taxid = ncbi.get_name_translator([taxon])[taxon][0]
        else:
            taxon = ncbi.get_taxid_translator([taxid])[taxid]

        species = ncbi.get_descendant_taxa(taxid, collapse_subspecies=True)
        for sp in species:
            expanded_taxa.add(sp)

    return expanded_taxa


def dump_orthologs(seed_orthologs_file, args):
    orthologs_file = pjoin(args.output, ".orthologs")
    OUT = open(orthologs_file, "w")
    if args.output_format in ("per_query", "per_orthology_type"):
        if args.output_format == "per_query":
            ortholog_header = ("#Query", "Target_Taxon", "Taxid", "Orthologs")
        else:
            ortholog_header = ("#Query", "Ortho_Type","In-Paralogs","Target_Taxon", "Taxid", "Orthologs")
        print >> OUT, "\t".join(ortholog_header)


def write_orthologs_in_file(result_line, OUT, args):
    """
    Writes orthologs in file for the output formats "per_query" and "per_orthology_type"
    """
    query_name, all_orthologs, target_taxon_name, target_taxid, best_hit_name = result_line

    if args.output_format == "per_query":
        orthologs = sorted(all_orthologs[args.orthology_type])
        print >> OUT, '\t'.join(map(str, (query_name, target_taxon_name, target_taxid, ','.join(orthologs))))

    elif args.output_format == "per_orthology_type" :
        for ortho_type in all_orthologs:
            if len(all_orthologs[ortho_type])==0 or ortho_type=="all":
                continue
            in_paralogs = []
            orthologs = []
            if ortho_type == "one2one" or ortho_type == "one2many":
                in_paralogs.append("N/A")
                orthologs = all_orthologs[ortho_type]
            else:
                for protein in all_orthologs[ortho_type]:
                    if protein.split(".")[0] == best_hit_name.split(".")[0] and protein != best_hit_name:
                        in_paralogs.append(protein)
                    elif protein != best_hit_name:
                        orthologs.append(protein)
            print >> OUT, '\t'.join(map(str, (query_name, ortho_type,
                                              ",".join(in_paralogs), target_taxon_name, target_taxid,
                                              ','.join(all_orthologs[ortho_type]))))

    OUT.flush()

def sort_orthologs_by_species(all_orthologs, best_hit_name):
    seed_ortholog_sp = best_hit_name.split('.', 1)[0]
    sorted_orthologs = defaultdict(set)

    for ortho_type in all_orthologs:
        if ortho_type == "all" or not all_orthologs[ortho_type]:
            continue
        else:
            inparalogs = frozenset([member for member in all_orthologs[ortho_type]
                                    if member != best_hit_name and \
                                    member.startswith('%s.' %seed_ortholog_sp)])

            for member in all_orthologs[ortho_type]:
                sp = member.split('.', 1)[0]
                sorted_orthologs[(sp, None, 'all')].add(member)
                if member not in inparalogs:
                    sorted_orthologs[(sp, inparalogs, ortho_type)].add(member)

    return sorted_orthologs

