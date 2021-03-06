#!/bin/bash

echo Executing the Neighborhood Clustering Part of the pipeline::::Computing and clustering Neighborhood


###Extract the name of the input .fna filename

name=$(echo "$1" | cut -d'.' -f1)

echo $name


####split the name in order to obtain only the genome name excluding .fna or any other extensions

locusname=$(echo "$1" | cut -d'_' -f1)

echo $locusname


###### Creating separate directories 1> to store all gbk files 2> to store all rgi files required

mkdir allgbksrequired

mkdir allrgisrequired


##### Running PROKKA (Prokaryotic Annotation) tool to obtain the .gbk files from the given fna file/files
prokka $1 --prefix $locusname --outdir ${locusname}_prokka  --locustag $locusname

###### Running RGI (Resistance Genomic Index) tool to obtain the annotation of CARD identified resistance genes
rgi main --clean --input_sequence $1 --alignment_tool BLAST  --num_threads 1 --output $locusname


###### Copying the file reuired .gbk and .txt files to the directories created earlier*
cp ${locusname}_prokka/${locusname}.gbk allgbksrequired
cp ${locusname}.txt allrgisrequired

##### Executing python script to identify neighbors for the given genomes and provide neighborhood files for each drug class in the .fasta format
python3 Neighborhood.py Fin_RGI Fin_gbk


#### creating separate directory for .fasta files obtain from python script and running ALL-Vs-All Blast to get similarity results.
mkdir blastque
mv drugclassiden.fasta blastque/

mkdir output
makeblastdb -dbtype prot -in blastque/drugclassiden.fasta

blastp -query blastque/drugclassiden.fasta -db blastque/drugclassiden.fasta -outfmt  "6 qseqid sseqid pident length evalue bitscore qseq sseq " -out output/pipeoutdrug.txt


#### Executing a python script that reads the blast result files and clusters similar neighborhoods based on UPGMA clustering method
####### Also generates list of fasta files of the similar neighborhood with more percent identity for each genome [ Files that are required for phylogenetic analysis]

mkdir similar_neighbor_files
for i in ./*.fasta
	mv i similar_neighbor_files/

python3 clustering.py output Fin_RGI Fin_gbk


echo "Beginning phylo pipeline: converting homologous sequences to trees..."

#Store names of .treefiles created
declare -a files

#Create .treefiles from each homologous sequence file in directory
for file in similar_neighbor_files/*.fasta; do
    #Make tree visualizations
    echo "Generating .treefile..."
    output=$(python3 make_ML_tree_vis.py -h_seq $file)
    files+=($output)
done

#Show list of .treefiles
echo ".treefiles created:"
for filename in ${files[@]}; do echo $filename; done

#Make directory to move .treefiles into
if [ ! -d treefiles ]; then
  mkdir treefiles;
  chmod -R o+rw treefiles;
fi;

#Move .treefiles
echo "Storing .treefiles in treefiles directory"
for file in ./*.treefile; do
  mv $file treefiles;
done

#Make distance matrices
echo "Creating RF distance and BSD matrices from .treefiles..."
python3 tree_distances.py -tree_path treefiles

#Make UPGMA and Neighbor-Joining tree clusters
echo "Clustering trees from distance matrices..."
python3 tree_clustering.py -matrix_path treefiles
