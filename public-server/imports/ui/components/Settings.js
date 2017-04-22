const Settings = {
  ftpBAM: 'ftp://ftp-trace.ncbi.nlm.nih.gov/giab/ftp/data/NA12878/NIST_NA12878_HG001_HiSeq_300x/NHGRI_Illumina300X_novoalign_bams/HG001.GRCh38_full_plus_hs38d1_analysis_set_minus_alts.300x.bam',
  s3BAM: '@176449128',
  tred: '',
  ref: 'hg38',
  env: 'public',
  examples: [
    't001_HD.bam',
    't002_DM1.bam',
    't003_SCA17.bam',
    't004_AR.bam',
  ],
};

module.exports = Settings;
