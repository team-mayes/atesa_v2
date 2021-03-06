Example of equilibrium path sampling prod input file
 &cntrl
  imin=0,
  ioutfm=1,						!netCDF output format
  ntx=5,
  ntxo=1,
  nstlim={{ nstlim }},          ! THIS LINE REQUIRED
  dt=0.001,
  ntf=2,
  ntc=2,						! SHAKE. 1 = no, 2 = hydrogen bonds, 3 = all bonds
  irest=1,
  temp0=300.0,
  ntpr=10,  					! Steps between writes to out
  ntwx={{ ntwx }},						! Steps between writes to mdcrd. 0 = no mdcrd; THIS LINE REQUIRED
  ntwv=-1,
  cut=8.0,
  ntb=2,						! Periodicity. = 2 for ntp > 0
  ntp=1,
  ntt=2,						! Temperature control scheme. 2 = Anderson, 3 = Langevin
  vrand=100,					! Steps between redistribution of velocities according to Boltzmann distribution
  ig=-1,
  ifqnt=1,
 &end
 &qmmm
  qmmask='(:492,493) | (:218,219,193,194,195,197,143,220,480,484,485,153,154,223,224,227,478,376,378,490,153,417,427 & !@C,CA,N,HA,H,O) | (:11420,11498,11360,11000,7811,11364,15531,11260,13952,11402,13890,6297,10930,8533,8620,10515,15693,9812,13989,10097,5492,8363,14578,4959,10649)',
  qmcharge=1,
  qm_theory='DFTB',
  qmshake=0,
  qmcut=8.0,
 &end
 &wt
  type="END",
 &end
