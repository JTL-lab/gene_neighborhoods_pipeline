#!/usr/bin/env python

"""
Script to ouput ete3 powered phylogenetic tree visualizations given 
a homologous sequence file. 
Note that the MUSCLE binary file must be contained in this directory.
"""

import sys
import subprocess
import argparse 
import hashlib
import ete3 as et

"""
Returns a list of all taxa that share the same sequence
Parameters:
    seq_dict: keys <- taxa identifiers, values <- sequences
    seq: sequence to look for
"""
def get_taxa(seq_dict, seq):
    
    identical_taxa = []
    
    for taxa, sequence in seq_dict.items():
        
        if (sequence == seq):
            identical_taxa.append(taxa)
    
    return identical_taxa
        
        
"""Replaces identical sequences with a surrogate to clean up 
phylogenetic tree"""
        
def check_surrogates(hom_seq_file):
    
    taxa = []
    seqs = []
    
    #Check homologous sequence file for any identical sequences
    with open(hom_seq_file, 'r') as file:
        
        lines = file.read()
        
        for line in lines.split("\n"):
            
            if (line != ""):
                
                #Store taxa identifiers and sequences
                if (line[0] == ">"):
                    taxa.append(line)
                    
                else:
                    seqs.append(line)
                    
    hom_seqs = dict(zip(taxa, seqs))
    
    #Retain unique sequences
    seqs = list(set(seqs))
    
    #Make new homologous sequence file
    new_file = open("clean_seq_align.fasta", "w+")
    
    for seq in seqs:
        
        taxa = get_taxa(hom_seqs, seq)
        
        #Generate a surrogate for every identical sequence
        if (len(taxa) > 1):
            #Annotate surrogate with # of seqs it stands in for
            surrogate = ">sequence_surrogate_"+str(len(taxa))
            new_file.write(surrogate+"\n")
            new_file.write(seq+"\n")

        #Otherwise assume identical sequence
        else:
            new_file.write(taxa[0]+"\n")
            new_file.write(seq+"\n")

      
def make_tree_vis(newick_tree, gene_name, file_name):
    
    tree = et.Tree(newick_tree)
    
    #Customizations
    nifty = et.TreeStyle()
    nifty.show_branch_support = True
    nifty.branch_vertical_margin = 15
    nifty.scale = 10
    
    #Leaf node customizations
    style_L = et.NodeStyle()
    style_L['shape'] = 'sphere'
    style_L['size'] = 10
    style_L['fgcolor'] = '#6BC245'
    style_L['hz_line_type'] = 1
    style_L['hz_line_color'] = '#cccccc'

    #Internal node customizations
    style_I = et.NodeStyle()
    style_I['shape'] = 'sphere'
    style_I['size'] = 10
    style_I['fgcolor'] = '#5271FF'
    style_I['hz_line_type'] = 1
    style_I['hz_line_color'] = '#cccccc'

    #Apply stylizations
    for node in tree.traverse():
        if node.is_leaf():
            node.set_style(style_L)
        else:
            node.set_style(style_I)
    
    #Annotate root of tree with gene name
    gene_label = et.TextFace(gene_name, ftype="Helvetica", fsize=5,\
                             fgcolor='green')
    tree.add_face(gene_label, column=0, position = "branch-top")
    
    tree.render(file_name + "_tree.png", tree_style=nifty)
    
    

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Generate 1000 BS replicate \
                                     ML tree with visualizations from \
                                     homologous protein seq FASTA file') 
                                     
    #User input: name of homologous sequence file, gene name                
    parser.add_argument('-h_seq','-seq', type=str,
                        help='Name file containing homologous sequences:\
                        must be in same directory')
         
    parser.add_argument('-gene', '-g', type=str, required=False,
                        help='Name of gene from homologous sequence file')
    
    args = vars(parser.parse_args())
    
    #Create a new homologous sequence file with surrogates where appropriate
    check_surrogates(str(sys.argv[2]))
    
    #Call on MUSCLE alignment tool: MUSCLE binary file must be in directory
    subprocess.run(['muscle','-in',"clean_seq_align.fasta",'-out',\
                    str(sys.argv[2])+'_align.fasta'])
    
    #Call IQ-TREE: automatically detect best model and perform 1000 BS
    subprocess.run(['iqtree','-s',str(sys.argv[2])+'_align.fasta','-m','MFP',\
                    '-B','1000'])
                     
    #Create visualization from .treefile 
    with open(str(sys.argv[2])+'_align.fasta.treefile','r') as file:
        
    	newick_str = file.read().replace('\n', '')
    
    make_tree_vis(newick_str, str(sys.argv[4]), str(sys.argv[2]))
    
    
    
